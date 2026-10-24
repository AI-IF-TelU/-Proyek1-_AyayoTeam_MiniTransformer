"""Tes kontrak training step, loss, dan pembaruan parameter (Issue D, subtask D7).

Melengkapi `tests/test_training_step.py` milik Issue C (subtask C8) yang hanya
memeriksa `loss` finite dan `lm_head.weight` berubah. Tes ini membuktikan
perilaku kontraktual `TECH_SPEC.md` 5 dan 6 pada `src/train.py`:

- `training_step` mengembalikan `float` finite dan loss-nya memang loss dari
  logits pada step tersebut, bukan nilai lain;
- `CrossEntropyLoss(ignore_index=pad_id)` membuat posisi target `pad_id` tidak
  berkontribusi: mengubah logits di baris pad tidak mengubah loss (eksak),
  dengan kontrol sensitivitas pada baris non-pad agar tes tidak vakum;
- `pad_id` benar-benar diparameterkan (bukan hardcode 0);
- gradien pada baris logits ber-target pad tepat nol, sehingga pad tidak
  mengalir ke pembaruan parameter;
- seluruh parameter trainable berubah setelah satu `optimizer.step()`, dengan
  kontrol negatif `lr=0` agar perubahan terbukti berasal dari step optimizer;
- state optimizer mencatat satu langkah;
- `set_seed(42)` mereproduksi loss dan parameter (seed kontrak 6);
- guard `context_length` milik MiniGPT tetap berlaku di jalur training dan
  tidak meninggalkan perubahan parameter;
- `training_step` menempatkan model pada mode `train()`;
- overfit satu batch kecil menurunkan loss (arah optimisasi benar).

Semua tes berjalan di CPU dengan model kecil; dropout dinolkan kecuali pada
tes reproduktibilitas yang memang menguji pengaruh seed terhadap dropout.
"""
import unittest

import pytest
import torch
import torch.nn.functional as F

from src.model.minigpt import MiniGPT
from src.train import make_criterion, make_optimizer, set_seed, training_step

VOCAB_SIZE = 16
PAD_ID = 0
D_MODEL = 8
N_HEADS = 2
N_LAYERS = 2
CONTEXT_LENGTH = 8
B, T = 2, 6


def _make_model(dropout: float = 0.0) -> MiniGPT:
    return MiniGPT(
        vocab_size=VOCAB_SIZE,
        n_layers=N_LAYERS,
        n_heads=N_HEADS,
        d_model=D_MODEL,
        context_length=CONTEXT_LENGTH,
        dropout=dropout,
    )


def _make_batch():
    """Batch kontrak 4: `x[i,t] == y[i,t-1]` pada posisi non-pad, pad di ekor."""
    x = torch.tensor(
        [[4, 5, 6, 7, PAD_ID, PAD_ID], [8, 9, 10, 11, PAD_ID, PAD_ID]],
        dtype=torch.long,
    )
    y = torch.tensor(
        [[PAD_ID, 4, 5, 6, 7, PAD_ID], [PAD_ID, 8, 9, 10, 11, PAD_ID]],
        dtype=torch.long,
    )
    return x, y


def _pad_mask(y):
    return y == PAD_ID


def _run_step_capturing_logits(model, x, y, optimizer, criterion):
    """Jalankan satu step dan tangkap logits step itu beserta gradiennya."""
    captured = {}

    def hook(module, inputs, output):
        output.retain_grad()
        captured["logits"] = output

    handle = model.register_forward_hook(hook)
    try:
        loss = training_step(model, x, y, optimizer, criterion)
    finally:
        handle.remove()
    return loss, captured["logits"]


def _flat(logits, y):
    return logits.reshape(-1, logits.size(-1)), y.reshape(-1)


def _snapshot(model):
    return {name: p.detach().clone() for name, p in model.named_parameters()}


class TestTrainingStepLoss(unittest.TestCase):
    def test_batch_is_contract_consistent_before_use(self):
        """Sanity: batch uji memenuhi relasi shift kontrak 4."""
        x, y = _make_batch()
        nonpad = ~_pad_mask(y)
        self.assertTrue(torch.equal(x[:, :-1][nonpad[:, 1:]], y[:, 1:][nonpad[:, 1:]]))
        self.assertEqual(y[0, 0].item(), PAD_ID)
        self.assertEqual(y[0, -1].item(), PAD_ID)

    def test_training_step_returns_finite_python_float(self):
        model = _make_model()
        optimizer = make_optimizer(model, lr=1e-2)
        criterion = make_criterion(pad_id=PAD_ID)
        x, y = _make_batch()
        loss = training_step(model, x, y, optimizer, criterion)
        self.assertIsInstance(loss, float)
        self.assertTrue(torch.isfinite(torch.tensor(loss)), f"loss not finite: {loss}")

    def test_returned_loss_matches_cross_entropy_of_step_logits(self):
        """Loss yang dikembalikan = CE(flat logits step itu, flat y, ignore pad)."""
        model = _make_model()
        optimizer = make_optimizer(model, lr=1e-2)
        criterion = make_criterion(pad_id=PAD_ID)
        x, y = _make_batch()
        loss, logits = _run_step_capturing_logits(model, x, y, optimizer, criterion)
        flat_logits, flat_y = _flat(logits, y)
        expected = F.cross_entropy(flat_logits, flat_y, ignore_index=PAD_ID)
        self.assertAlmostEqual(loss, float(expected.item()), places=6)
        # Kontrol: menyertakan target pad (ignore_index=-100) memberi nilai lain.
        with_pad = F.cross_entropy(flat_logits, flat_y, ignore_index=-100)
        self.assertFalse(
            torch.isclose(with_pad, expected, atol=1e-6, rtol=0),
            "loss tidak membedakan ada/tidaknya ignore_index -> tes tidak sensitif",
        )

    def test_returned_loss_is_detached_from_graph(self):
        """Nilai loss yang dikembalikan harus skalar Python, bukan tensor grad."""
        model = _make_model()
        optimizer = make_optimizer(model, lr=1e-2)
        criterion = make_criterion(pad_id=PAD_ID)
        x, y = _make_batch()
        loss = training_step(model, x, y, optimizer, criterion)
        self.assertEqual(type(loss), float)


class TestPadTargetIgnoredInLoss(unittest.TestCase):
    def test_perturbing_pad_row_logits_does_not_change_loss(self):
        model = _make_model()
        optimizer = make_optimizer(model, lr=1e-2)
        criterion = make_criterion(pad_id=PAD_ID)
        x, y = _make_batch()
        _, logits = _run_step_capturing_logits(model, x, y, optimizer, criterion)
        mask = _pad_mask(y)

        base = criterion(*_flat(logits, y))

        # Ubah logits kelas target pad secara ekstrem: bila baris pad dihitung,
        # nilai ini pasti mengubah loss. Pergeseran seragam seluruh kelas tidak
        # dipakai karena softmax invarian terhadapnya (tes akan lolos palsu).
        perturbed = logits.detach().clone()
        perturbed[mask, PAD_ID] -= 100.0
        after_pad = criterion(*_flat(perturbed, y))
        self.assertTrue(
            torch.equal(base, after_pad),
            f"logits baris pad memengaruhi loss: {base.item()} vs {after_pad.item()}",
        )

        # Kontrol anti-vakum: tanpa ignore_index, perturbasi yang sama terbukti
        # mengubah loss, jadi kesamaan di atas bukan karena perturbasi kosong.
        self.assertFalse(
            torch.isclose(
                F.cross_entropy(*_flat(perturbed, y), ignore_index=-100),
                F.cross_entropy(*_flat(logits, y), ignore_index=-100),
            )
        )

    def test_perturbing_nonpad_row_logits_changes_loss(self):
        """Kontrol sensitivitas: baris non-pad memang menentukan loss."""
        model = _make_model()
        optimizer = make_optimizer(model, lr=1e-2)
        criterion = make_criterion(pad_id=PAD_ID)
        x, y = _make_batch()
        _, logits = _run_step_capturing_logits(model, x, y, optimizer, criterion)
        mask = _pad_mask(y)

        base = criterion(*_flat(logits, y))
        perturbed = logits.detach().clone()
        perturbed[~mask, PAD_ID] += 100.0
        self.assertFalse(torch.isclose(criterion(*_flat(perturbed, y)), base))

    def test_custom_pad_id_is_ignored_too(self):
        """`pad_id` diparameterkan: id 5 diabaikan bila `ignore_index=5`."""
        x, _ = _make_batch()
        y = torch.full((B, T), 5, dtype=torch.long)
        y[0, 1] = 7
        y[1, 2] = 9
        logits = torch.randn(B, T, VOCAB_SIZE)

        crit5 = make_criterion(pad_id=5)
        crit0 = make_criterion(pad_id=PAD_ID)
        loss5 = crit5(*_flat(logits, y))
        manual5 = F.cross_entropy(*_flat(logits, y), ignore_index=5)
        self.assertTrue(torch.equal(loss5, manual5))
        self.assertFalse(
            torch.isclose(crit0(*_flat(logits, y)), loss5),
            "criterion mengabaikan pad_id dan selalu memakai 0",
        )

    def test_gradient_is_zero_at_pad_target_positions(self):
        model = _make_model()
        optimizer = make_optimizer(model, lr=1e-2)
        criterion = make_criterion(pad_id=PAD_ID)
        x, y = _make_batch()
        _, logits = _run_step_capturing_logits(model, x, y, optimizer, criterion)

        grad = logits.grad
        self.assertIsNotNone(grad, "gradien logits tidak terekam")
        mask = _pad_mask(y)
        self.assertTrue(
            torch.equal(grad[mask], torch.zeros_like(grad[mask])),
            f"gradien posisi pad tidak nol: max |g| = {grad[mask].abs().max().item()}",
        )
        self.assertTrue(grad[~mask].abs().max().item() > 0, "gradien non-pad semuanya nol")


class TestParameterUpdate(unittest.TestCase):
    def test_every_trainable_parameter_changes_after_one_step(self):
        model = _make_model()
        optimizer = make_optimizer(model, lr=1e-2)
        criterion = make_criterion(pad_id=PAD_ID)
        x, y = _make_batch()
        before = _snapshot(model)

        training_step(model, x, y, optimizer, criterion)

        after = _snapshot(model)
        self.assertEqual(set(before), set(after))
        self.assertGreater(len(after), 0)
        for name, old in before.items():
            self.assertTrue(
                torch.isfinite(after[name]).all(), f"parameter {name} tidak finite"
            )
            self.assertFalse(
                torch.allclose(old, after[name]),
                f"parameter {name} tidak berubah setelah satu step",
            )

    def test_zero_lr_control_leaves_parameters_unchanged(self):
        """Kontrol negatif: tanpa langkah optimizer sungguhan parameter identik."""
        model = _make_model()
        optimizer = make_optimizer(model, lr=0.0)
        criterion = make_criterion(pad_id=PAD_ID)
        x, y = _make_batch()
        before = _snapshot(model)

        training_step(model, x, y, optimizer, criterion)

        after = _snapshot(model)
        for name, old in before.items():
            self.assertTrue(
                torch.equal(old, after[name]),
                f"parameter {name} berubah walau lr=0",
            )

    def test_optimizer_records_one_step_for_all_parameters(self):
        model = _make_model()
        optimizer = make_optimizer(model, lr=1e-2)
        criterion = make_criterion(pad_id=PAD_ID)
        x, y = _make_batch()

        training_step(model, x, y, optimizer, criterion)

        n_params = len(list(model.parameters()))
        self.assertEqual(len(optimizer.state), n_params)
        steps = [int(state["step"]) for state in optimizer.state.values() if "step" in state]
        self.assertEqual(len(steps), n_params)
        self.assertTrue(all(s == 1 for s in steps), f"step counter: {steps}")

    def test_second_step_advances_optimizer_state(self):
        model = _make_model()
        optimizer = make_optimizer(model, lr=1e-2)
        criterion = make_criterion(pad_id=PAD_ID)
        x, y = _make_batch()

        training_step(model, x, y, optimizer, criterion)
        after_first = _snapshot(model)
        training_step(model, x, y, optimizer, criterion)
        after_second = _snapshot(model)

        steps = [int(s["step"]) for s in optimizer.state.values() if "step" in s]
        self.assertTrue(all(s == 2 for s in steps), f"step counter: {steps}")
        for name, first in after_first.items():
            self.assertFalse(
                torch.allclose(first, after_second[name]),
                f"parameter {name} tidak berubah pada step kedua",
            )

    def test_model_is_in_train_mode_after_step(self):
        model = _make_model()
        model.eval()
        optimizer = make_optimizer(model, lr=1e-2)
        criterion = make_criterion(pad_id=PAD_ID)
        x, y = _make_batch()

        training_step(model, x, y, optimizer, criterion)

        self.assertTrue(model.training, "training_step harus memanggil model.train()")

    def test_overfitting_one_batch_reduces_loss(self):
        """Arah optimisasi benar: loss batch tetap turun setelah beberapa step."""
        set_seed(42)
        model = _make_model()
        optimizer = make_optimizer(model, lr=1e-2)
        criterion = make_criterion(pad_id=PAD_ID)
        x, y = _make_batch()

        first = training_step(model, x, y, optimizer, criterion)
        loss = first
        for _ in range(24):
            loss = training_step(model, x, y, optimizer, criterion)

        self.assertTrue(torch.isfinite(torch.tensor(loss)))
        self.assertLess(loss, first, f"loss tidak turun: {first} -> {loss}")


class TestTrainingReproducibility(unittest.TestCase):
    def _run(self, dropout=0.1):
        set_seed(42)
        model = _make_model(dropout=dropout)
        optimizer = make_optimizer(model, lr=1e-2)
        criterion = make_criterion(pad_id=PAD_ID)
        x, y = _make_batch()
        loss = training_step(model, x, y, optimizer, criterion)
        return loss, _snapshot(model)

    def test_seed_42_reproduces_loss_and_parameters(self):
        loss_a, params_a = self._run()
        loss_b, params_b = self._run()

        self.assertEqual(loss_a, loss_b)
        for name, value in params_a.items():
            self.assertTrue(
                torch.equal(value, params_b[name]),
                f"init/update parameter {name} tidak reproducible dengan seed 42",
            )

    def test_different_seed_reproduces_differently_with_dropout(self):
        """Kontrol: dropout aktif membuat seed berbeda menghasilkan hasil berbeda."""
        loss_a, params_a = self._run()
        set_seed(7)
        model = _make_model(dropout=0.1)
        optimizer = make_optimizer(model, lr=1e-2)
        criterion = make_criterion(pad_id=PAD_ID)
        x, y = _make_batch()
        loss_b = training_step(model, x, y, optimizer, criterion)

        self.assertNotEqual(loss_a, loss_b)
        self.assertFalse(
            all(torch.equal(params_a[n], p.detach()) for n, p in model.named_parameters())
        )


class TestTrainingStepGuards(unittest.TestCase):
    def test_context_length_guard_applies_and_keeps_parameters(self):
        model = _make_model()
        optimizer = make_optimizer(model, lr=1e-2)
        criterion = make_criterion(pad_id=PAD_ID)
        x_long = torch.full((B, CONTEXT_LENGTH + 1), 7, dtype=torch.long)
        y_long = torch.full((B, CONTEXT_LENGTH + 1), 8, dtype=torch.long)
        self.assertEqual(x_long.size(1), CONTEXT_LENGTH + 1)
        before = _snapshot(model)

        with pytest.raises(ValueError):
            training_step(model, x_long, y_long, optimizer, criterion)

        after = _snapshot(model)
        for name, old in before.items():
            self.assertTrue(torch.equal(old, after[name]))
        self.assertEqual(len(optimizer.state), 0)

    def test_error_and_pad_only_target_relationship_is_documented(self):
        """Keterbatasan terdokumentasi: target seluruhnya pad -> loss NaN.

        `nn.CrossEntropyLoss(ignore_index=pad_id)` mengembalikan NaN bila tidak
        ada satu pun target yang dihitung. `training_step` tidak memiliki guard
        untuk kasus ini dan `TECH_SPEC.md` 5 tidak mengaturnya, sehingga perilaku
        aktual dicatat apa adanya (bukan dijadikan kontrak).
        """
        model = _make_model()
        optimizer = make_optimizer(model, lr=1e-2)
        criterion = make_criterion(pad_id=PAD_ID)
        y = torch.full((B, T), PAD_ID, dtype=torch.long)
        x, _ = _make_batch()

        loss = training_step(model, x, y, optimizer, criterion)

        self.assertTrue(torch.isnan(torch.tensor(loss)))

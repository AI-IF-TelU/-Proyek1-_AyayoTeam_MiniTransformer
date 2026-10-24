"""Tes untuk helper bersama `tests/helpers.py` (F-D11-01, D14).

Mengunci arah kontrak §4: `x[i,t] == y[i,t-1]`, yaitu `y` adalah `x` yang
digeser satu posisi ke kiri. Sebelum perbaikan, `make_batch` membangun arah
terbalik dan `assert_x_y_shift` melegalkannya karena `AssertionError`
tertelan `except Exception`.
"""

import pytest
import torch

from tests.helpers import assert_x_y_shift, make_batch

PAD_ID = 0


def test_make_batch_follows_contract_direction():
    x, y = make_batch(4, 64)
    assert_x_y_shift(x, y)


def test_make_batch_target_is_next_token():
    x, y = make_batch(4, 64)
    nonpad = y[:, :-1] != PAD_ID
    assert torch.equal(x[:, 1:][nonpad], y[:, :-1][nonpad])


def test_make_batch_reversed_direction_is_rejected():
    x, y = make_batch(4, 64)
    with pytest.raises(AssertionError):
        assert_x_y_shift(y, x)


def test_assert_x_y_shift_rejects_broken_shift():
    x = torch.tensor([[4, 5, 6, 7]])
    y = torch.tensor([[5, 6, 7, PAD_ID]])
    assert_x_y_shift(x, y)
    y_broken = y.clone()
    y_broken[0, 1] = 99
    with pytest.raises(AssertionError):
        assert_x_y_shift(x, y_broken)


def test_assert_x_y_shift_rejects_shape_mismatch():
    with pytest.raises(AssertionError):
        assert_x_y_shift(torch.zeros(2, 3, dtype=torch.long),
                         torch.zeros(2, 4, dtype=torch.long))


def test_assert_x_y_shift_ignores_pad_targets():
    x = torch.tensor([[4, 5, PAD_ID, PAD_ID]])
    y = torch.tensor([[5, PAD_ID, PAD_ID, PAD_ID]])
    assert_x_y_shift(x, y)


def test_make_batch_matches_real_dataset_direction():
    from src.data.dataset import TextDataset
    from src.data.tokenizer import Tokenizer

    text = "satu dua tiga empat lima enam tujuh delapan sembilan sepuluh"
    tok = Tokenizer()
    tok.fit([text])
    ds = TextDataset([text], tok, context_length=8)
    x, y = ds[0]
    assert_x_y_shift(x.unsqueeze(0), y.unsqueeze(0))

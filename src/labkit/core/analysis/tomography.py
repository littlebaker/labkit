import numpy as np
import cvxpy as cpy

from typing import Sequence
import warnings
import qutip


def qubit_state_tomography(
    measurement_bases: Sequence[np.ndarray], values: Sequence[np.ndarray]
):
    A_list = []

    n = measurement_bases[0].shape[0]

    assert np.all([x.shape == (n, n) for x in measurement_bases]), (
        "measurement_basis must be square matrix"
    )
    assert len(values) == len(measurement_bases), (
        "length of measurement value must equales to length of measurement bases"
    )

    for mb in measurement_bases:
        A_list.append(np.reshape(mb, (n * n,), "F"))

    A = np.array(A_list)

    rho = cpy.Variable((n, n), complex=True)

    rho_vec = cpy.vec(rho, "F")

    obj = cpy.Minimize(cpy.sum_squares(cpy.real(A @ rho_vec - values)))

    constrains = [cpy.trace(rho) == 1, rho >> 0]

    prob = cpy.Problem(obj, constrains)

    res = prob.solve()
    print(res)

    return rho.value


def process_tomography(
    rho_before: Sequence[np.ndarray],
    rho_after: Sequence[np.ndarray],
    expand_basis: Sequence[np.ndarray],
):
    rho_before = np.asarray(rho_before)
    rho_after = np.asarray(rho_after)
    expand_basis = np.asarray(expand_basis)

    assert rho_before.ndim == 3

    assert rho_before.shape == rho_after.shape

    assert rho_before.shape[1] == rho_before.shape[2]


    n_basis = rho_before.shape[0]
    N = rho_before.shape[1]

    assert len(expand_basis) == N ** 2

    _tensor_bases = np.einsum('mab, lbc, ncd -> lmnad', expand_basis, rho_before, expand_basis.conj().swapaxes(-1, -2))
    _tensor_bases = np.reshape(_tensor_bases, (n_basis, N**2, N**2, -1), order='F').transpose((0, 3, 1, 2))
    A = np.reshape(_tensor_bases, (n_basis * N**2, -1), order='F')

    Y = np.reshape(rho_after, (-1, ), order='F')


    chi = cpy.Variable((N**2, N**2), hermitian=True)


    obj = cpy.Minimize(cpy.sum_squares(A @ cpy.vec(chi, order='F') - Y))
    constrains = [chi >> 0, ]

    prob = cpy.Problem(obj, constrains)

    res = prob.solve()
    print(res)

    return chi.value


if __name__ == "__main__":
    from qutip import sigmaz, sigmax, sigmay, Bloch, Qobj, qeye

    sx, sy, sz = (
        sigmax().full(),
        sigmay().full(),
        sigmaz().full(),
    )
    bases = [sx, sy, sz]
    values = [0, 0.0, -2]
    # values = [0.64349228, 0.61755356, 1.00000000e+00]

    # res = qubit_state_tomography(bases, values)
    # rho = Qobj(res, dims=[2, 2])

    # b = Bloch()
    # b.add_states(rho)
    # display(rho)  # type: ignore

    # b.show()

    I = qeye(2).full()
    def _gen_rho():
        _rho = np.random.normal(size=(2, 2))+  1j*np.random.normal(size=(2, 2))
        return _rho / np.trace(_rho)
    
    rho_list = [_gen_rho() for _ in range(3)]

    Chi = process_tomography(rho_list, rho_list, [I, sx, sy, sz])
    print(Chi)

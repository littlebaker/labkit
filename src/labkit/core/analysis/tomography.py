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



def process_tomography(rho_before: Sequence[np.ndarray], rho_after: Sequence[np.ndarray]):
    rho_before = np.asarray(rho_before)
    rho_after = np.asarray(rho_after)

    assert rho_before.ndim == 3

    assert rho_before.shape == rho_after.shape

    assert rho_before.shape[0] == rho_before.shape[1]


    n_basis = rho_before.shape[0]
    N = rho_before.shape[1]

    U = cpy.Variable((N**2, N**2), complex=True)

    def _vec(x):
        return x.reshape((-1, 1), 'F')

    obj = cpy.Minimize(sum([cpy.real(cpy.sum_squares(U@_vec(x) - y)) for x, y in zip(rho_before, rho_after)]))

    prob = cpy.Problem(obj, None)

    res = prob.solve()
    print(res)

    return U.value


    





if __name__ == "__main__":
    from qutip import sigmaz, sigmax, sigmay, Bloch, Qobj

    sx, sy, sz = (
        sigmax().full(),
        sigmay().full(),
        sigmaz().full(),
    )
    bases = [sx, sy, sz]
    values = [0, 0., -2]
    # values = [0.64349228, 0.61755356, 1.00000000e+00]

    res = (qubit_state_tomography(bases, values))
    rho = Qobj(res, dims=[2, 2])

    b = Bloch()
    b.add_states(rho)
    display(rho) # type: ignore



    b.show()


    

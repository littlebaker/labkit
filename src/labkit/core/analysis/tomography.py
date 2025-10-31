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

    rho = cpy.Variable((n, n), hermitian=True)

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

    assert len(expand_basis) == N**2

    _tensor_bases = np.einsum(
        "mab, lbc, ncd -> lmnad",
        expand_basis,
        rho_before,
        expand_basis.conj().swapaxes(-1, -2),
    )
    _tensor_bases = np.reshape(
        _tensor_bases, (n_basis, N**2, N**2, -1), order="F"
    ).transpose((0, 3, 1, 2))
    A = np.reshape(_tensor_bases, (n_basis * N**2, -1), order="F")

    Y = np.reshape(rho_after, (-1,), order="F")

    chi = cpy.Variable((N**2, N**2), hermitian=True)

    obj = cpy.Minimize(cpy.sum_squares(A @ cpy.vec(chi, order="F") - Y))
    constrains = [
        chi >> 0,
    ]

    prob = cpy.Problem(obj, constrains)

    res = prob.solve()
    print(res)

    return chi.value


if __name__ == "__main__":
    from qutip import sigmaz, sigmax, sigmay, Bloch, Qobj, qeye, plot_spin_distribution
    from qutip_qip.operations import rx, ry, rz

    # sx, sy, sz = (
    #     sigmax().full(),
    #     sigmay().full(),
    #     sigmaz().full(),
    # )
    # bases = [sx, sy, sz]
    # values = [0, 0.0, -2]
    # # values = [0.64349228, 0.61755356, 1.00000000e+00]

    # # res = qubit_state_tomography(bases, values)
    # # rho = Qobj(res, dims=[2, 2])

    # # b = Bloch()
    # # b.add_states(rho)
    # # display(rho)  # type: ignore

    # # b.show()

    # I = qeye(2).full()
    # def _gen_rho():
    #     _rho = np.random.normal(size=(2, 2))+  1j*np.random.normal(size=(2, 2))
    #     return _rho / np.trace(_rho)

    # rho_list = [_gen_rho() for _ in range(3)]

    # Chi = process_tomography(rho_list, rho_list, [I, sx, sy, sz])
    # print(Chi)

    # s0, s1分别为测到0和测到1对应的算符，其值就是p0和p1
    s0 = np.array([[1, 0], [0, 0]])
    s1 = np.array([[0, 0], [0, 1]])

    # m11 = np.kron(s1, s1)
    # m10 = np.kron(s1, s0)
    # m01 = np.kron(s0, s1)

    pi = np.pi
    idle = Qobj(np.eye(2))

    # 构造门集
    gate_set = [
        [ry(-pi / 2), ry(-pi / 2)],
        [ry(-pi / 2), rx(pi / 2)],
        [ry(-pi / 2), idle],
        [rx(pi / 2), ry(-pi / 2)],
        [rx(pi / 2), rx(pi / 2)],
        [rx(pi / 2), idle],
        [idle, ry(-pi / 2)],
        [idle, rx(pi / 2)],
        [idle, idle],
    ]

    measurement_set = []
    measurement_values = np.array([
        [
            0.030924629126439715,
            0.30346664842246934,
            -5.104593206556806e-23,
            0.6656087224510909,
        ],
        [
            -1.4931913241980514e-23,
            0.32000290529989045,
            -3.1330341294450635e-24,
            0.6799970947001096,
        ],
        [
            -4.89185778077169e-24,
            0.19904405138993986,
            -4.2685221827636644e-23,
            0.8009559486100601,
        ],
        [
            -1.0523030082354161e-23,
            0.35662999907641296,
            1.1841428269829267e-23,
            0.643370000923587,
        ],
        [
            0.040235195664302566,
            0.2764896722222275,
            1.2250720994145338e-23,
            0.6832751321134699,
        ],
        [
            -1.8498897677453687e-23,
            0.18887561003182615,
            -3.159329072390318e-23,
            0.8111243899681738,
        ],
        [
            2.758175344555743e-23,
            0.3252185345753941,
            3.7058233003899684e-23,
            0.6747814654246059,
        ],
        [
            4.654917857724386e-23,
            0.3198876002802136,
            4.5486782027789524e-23,
            0.6801123997197864,
        ],
        [
            -3.3060764827579546e-24,
            0.2145086638357758,
            3.2852638453078505e-23,
            0.7854913361642242,
        ],
    ])
    # 选中对应算符的值，这里的顺序和下面的定义有关
    measurement_values = measurement_values[:, (3, 1, 2)].flatten()

    for two_gate in gate_set:
        r1, r2 = two_gate

        # 测到两个都是1的概率，也就是p11。那么g1就对应的是打了门之后测到p11的概率
        g1 = np.kron(r1.dag().full() @ s1 @ r1.full(), r2.dag().full() @ s1 @ r2.full())
        # 同理 p10 和 p11
        g2 = np.kron(r1.dag().full() @ s1 @ r1.full(), r2.dag().full() @ s0 @ r2.full())
        g3 = np.kron(r1.dag().full() @ s0 @ r1.full(), r2.dag().full() @ s1 @ r2.full())

        measurement_set.extend((g1, g2, g3))

    measurement_set = np.array(measurement_set)

    # 扔进去重构即可
    res = qubit_state_tomography(measurement_set, measurement_values)

    rho =Qobj(res, dims=[[2, 2], [2, 2]])

    rho
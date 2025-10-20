import numpy as np
import cvxpy as cpy



def deconfusion(C: np.ndarray, p_measured: np.ndarray):
    '''
        deconfuion using confusion matrix

        C: confusion matrix, must be column-wise stochastic matrix, 
        p_measured: measured probability 
    
    '''
    n = C.shape[0]

    assert C.shape == (n, n), "C must be square matrix"
    assert p_measured.shape == (n, ), "p.shape must be coordinate with C"

    assert np.allclose(np.sum(C, axis=0), np.ones((n,)), atol=1e-6), "C must be column-wise stochastic matrix"

    if np.linalg.cond(C) > 10:
        print(f"Warning, Condition number of C is {np.linalg.cond(C):.2}, larger than 10, ")
        print("which means the problem is strongly ill-conditioned.")
        print("The result may not be reliable.")

    p_unconfused = cpy.Variable(n)

    objective = cpy.Minimize(cpy.sum_squares(C @ p_unconfused - p_measured))
    constraints = [0 <= p_unconfused, p_unconfused <= 1, cpy.sum(p_unconfused)==1.0]
    prob = cpy.Problem(objective, constraints)

    # The optimal objective value is returned by `prob.solve()`.
    result = prob.solve()
    # The optimal value for x is stored in `x.value`.
    
    return p_unconfused.value


if __name__ == "__main__":
    C = np.array([[0.9, 0.91], [0.1, 0.09]])
    p_m = np.array([0.4, 0.6])

    print(deconfusion(C, p_m))

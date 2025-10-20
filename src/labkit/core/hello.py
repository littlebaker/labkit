from sympy import symbols, Piecewise, And, simplify, Contains, Interval, piecewise_fold
import numpy as np
import sympy as sp
t = symbols('t', real=True)

# 定义一个分段函数
f1 = Piecewise(
    (sp.cos(t), Interval(-np.inf, 20).contains(t)),     # 第一段: 1，当 0 < t <= 20
    (2, Interval(30, 40).contains(t)),    # 第二段: 0，当 20 < t <= 40
    (0, True)                  # 其他时间未定义（或可设为0）
)
f2 = Piecewise(
    (3, Interval(50, 60).contains(t)),     # 第一段: 1，当 0 < t <= 20
    (4, Interval(70, 80).contains(t)),    # 第二段: 0，当 20 < t <= 40
    (0, True)                  # 其他时间未定义（或可设为0）
)


# import waveforms as wf

# wf.gaussian(10, )
sp.piecewise_fold(f1+ f2)

from sympy import symbols, Piecewise, And, Interval, Union, Contains, S
from sympy.solvers.inequalities import reduce_inequalities
from sympy.printing.latex import latex

t = symbols('t', real=True)

pw = Piecewise(
    (t, And(t >= 0, t <= 20)),
    (0, True)
)

def cond_to_membership(cond):
    # True/False 原样返回
    if cond is S.true or cond is S.false:
        return cond
    # 选一个主变量（复杂条件可自行指定）
    syms = list(cond.free_symbols)
    if not syms:
        return cond
    x = syms[0]
    # 把不等式化成集合（可能是 Interval/Union）
    dom = reduce_inequalities(cond, x)
    # 若是集合，就转为 x ∈ 集合 的形式
    try:
        # Set 基类是 sympy.sets.sets.Set
        from sympy.sets.sets import Set
        if isinstance(dom, Set):
            return Contains(x, dom)
    except Exception:
        pass
    return cond

def piecewise_membership_form(pw):
    newargs = []
    for expr, cond in pw.args:
        newargs.append((expr, cond_to_membership(cond)))
    return Piecewise(*newargs)

pw2 = piecewise_membership_form(pw)
pw2
# print(latex(pw2))
# 输出形如：\begin{cases} t & \text{for}\: t \in [0, 20] \\ 0 & \text{otherwise} \end{cases}

"""Module to generate data from stochastic processes."""

import numpy as np
from numpy.typing import NDArray
from scipy.special import factorial, poch


class TwoStateMarkovChain:
    """Two-state Markov Chain from which sequences can be generated.

    Attributes:
        P: transition matrix.
        pi: stationary distribution.
    """

    def __init__(
        self,
        p: float,
        q: float,
    ) -> None:
        """Initialize class.

        Args:
            p: probability of going from state 0 to state 1.
            q: probability of going from state 1 to state 0.
        """
        # Check if input probabilities are valid
        assert 0 <= p <= 1, "p must be between zero and one."
        assert 0 <= q <= 1, "q must be between zero and one."

        # Define transition matrix
        self.P = np.array([
            [1-p, p],
            [q, 1-q],
        ])

        # Calculate stationary distribution
        self.pi = np.array([q / (p + q), p / (p + q)])

    def generate(
        self,
        N: int,
        seed: int | None = None,
    ) -> NDArray:
        """Generate a sequence of zeros and ones according to the two-state Markov chain.

        Args:
            N: length of generated sequence.
            seed: value used to initialize pseudorandom number generator.

        Returns:
            Sequence of length `N` generated by Markov chain.
        """
        # Instantiate pseudorandom number generator with given seed
        rng = np.random.default_rng(seed)

        # Define array of states
        states = np.empty(N, dtype=int)

        # Start on state 0 or state 1 following probabilities from stationary distribution
        states[0] = rng.binomial(n=1, p=self.pi[1])

        # Sequentially populate all other states
        for i in range(1, N):
            states[i] = rng.binomial(n=1, p=self.P[states[i-1], 1])

        # Verify resulting sequence only contains zeros or ones
        assert np.isin(states, [0, 1]).all()

        return states


class AR1:
    """Autoregressive process of order 1 from which sequences can be generated.

    Attributes:
        phi: dependence coefficient.
    """

    def __init__(
        self,
        phi: float,
    ) -> None:
        """Initialize class.

        Args:
            phi: dependence coefficient.
        """
        self.phi = phi

    def generate(
        self,
        N: int,
        seed: int | None = None,
    ) -> NDArray:
        """Generate a sequence according to the AR(1) process.

        Args:
            N: length of generated sequence.
            seed: value used to initialize pseudorandom number generator.

        Returns:
            Sequence of length `N` generated by autoregressive process.
        """
        # Instantiate pseudorandom number generator with given seed
        rng = np.random.default_rng(seed)

        # Define array of states, initially as iid standard normals
        states = rng.standard_normal(size=N)

        # Sequentially populate states
        for i in range(1, N):
            states[i] = self.phi * states[i-1] + states[i]

        return states


class CycleRandomWalk:
    """Random walk on the cycle graph from which sequences can be generated.

    Attributes:
        P: transition matrix.
        pi: stationary distribution.
        b: probability of going from state `j` to state `j - 1`.
        s: probability of staying on state `j`.
        f: probability of going from state `j` to state `j + 1`.
        vertices: number of vertices on the cycle graph.
    """

    def __init__(
        self,
        b: float,
        s: float,
        f: float,
        vertices: int,
    ) -> None:
        """Initialize class.

        Args:
            b: probability of going from state `j` to state `j - 1`.
            s: probability of staying on state `j`.
            f: probability of going from state `j` to state `j + 1`.
            vertices: number of vertices on the cycle graph.
        """
        self.b = b
        self.s = s
        self.f = f
        self.vertices = vertices

        # Check if input probabilities are valid
        assert 0 <= b <= 1, "b must be between zero and one."
        assert 0 <= s <= 1, "s must be between zero and one."
        assert 0 <= f <= 1, "f must be between zero and one."
        assert abs(b + s + f - 1) < 1e-12, "probabilities must sum up to one."

        # Define transition matrix
        self.P = (
            np.eye(vertices, k=-1) * b +
            np.eye(vertices, k=0) * s +
            np.eye(vertices, k=1) * f
        )
        self.P[0, -1] = b
        self.P[-1, 0] = f

        assert np.allclose(self.P.sum(axis=1), 1), "transition matrix rows must sum up to one."

        # Set stationary distribution
        self.pi = np.repeat(1 / vertices, repeats=vertices)

    def generate(
        self,
        N: int,
        seed: int | None = None,
    ) -> NDArray:
        """Generate a sequence of zeros and ones according to a random walk on the cycle graph.

        Args:
            N: length of generated sequence.
            seed: value used to initialize pseudorandom number generator.

        Returns:
            Sequence of length `N` generated by the random walk.
        """
        # Instantiate pseudorandom number generator with given seed
        rng = np.random.default_rng(seed)

        # Start on a certain state following probabilities from stationary distribution
        initial_state = rng.choice(np.arange(self.vertices), p=self.pi)

        # Sample all random walk moves
        moves = rng.choice([-1, 0, 1], p=[self.b, self.s, self.f], size=N-1)

        # Generate states
        states = np.append(initial_state, moves).cumsum() % self.vertices

        # Verify resulting sequence only contains integers between 0 and vertices-1
        assert np.isin(states, np.arange(self.vertices)).all()

        return states


class Renewal:
    """Renewal process from which sequences can be generated.

    Reference:
        Convergence Rates in the Strong Law for Bounded Mixing Sequences - Berbee (1997).

    Base distribution chosen as
        F(i) = 1 - n! i! / (i + n)!.
    """

    def __init__(
        self,
        n: float,
    ) -> None:
        """Initialize class.

        Args:
            n: decay coefficient.
        """
        assert n > 1
        self.n = n
        match n:
            case 2:
                self.lim_f = 1413
                self.lim_x_zero = 999998
            case 3:
                self.lim_f = 180
                self.lim_x_zero = 1412
            case 4:
                self.lim_f = 68
                self.lim_x_zero = 179
            case 5:
                self.lim_f = 39
                self.lim_x_zero = 67
            case _:
                self.lim_f = 27
                self.lim_x_zero = 38

    def cdf_x_zero(self, i: NDArray | float) -> NDArray:
        """Distribution function of first random variable."""
        return 1 - factorial(self.n) / poch(i + 1, self.n) * (i + 1) / self.n

    def cdf_f(self, i: NDArray | float) -> NDArray:
        """Distribution function of subsequent random variables, which have law F."""
        return 1 - factorial(self.n) / poch(i + 1, self.n)

    def generate(
        self,
        N: int,
        seed: int | None = None,
    ) -> NDArray:
        """Generate a sequence of zeros and ones according to the renewal process.

        Args:
            N: length of generated sequence.
            seed: value used to initialize pseudorandom number generator.

        Returns:
            Sequence of length `N` generated by renewal process.
        """
        rng = np.random.default_rng(seed)
        uniform_sample = rng.uniform(low=0, high=0.999999, size=N)

        x_zero = np.digitize(
            uniform_sample[0],
            self.cdf_x_zero(np.arange(self.lim_x_zero)),
        )

        x = np.digitize(
            uniform_sample[1:],
            self.cdf_f(np.arange(self.lim_f)),
        )

        x = np.append(x_zero, x)

        x_cumsum = x.cumsum()

        return np.array([int(np.isin(n, x_cumsum[:n]).item()) for n in range(N)])


class _Renewal:
    """Renewal process from which sequences can be generated.

    Reference:
        Convergence Rates in the Strong Law for Bounded Mixing Sequences - Berbee (1997).

    Base distribution chosen as F(i) = 1 - 6 / ((i+1) * (i+2) * (i+3)).

    Kept for compatibility and benchmarks. This class is faster than Renewal,
    but less general: it works only for k=3.
    """

    def _inverse_cdf_x_zero(self, j: NDArray) -> NDArray:
        """Inverse distribution function of first random variable."""
        # Calculated via
        #   from sympy import symbols, Eq, solve, simplify, Sum
        #   i, j = symbols("i j")
        #   cdf = Eq(j, (i**2 + 5*i + 4) / (i**2 + 5*i + 6))
        #   simplify(solve(cdf, i)[1])
        return np.ceil((-5*j - np.sqrt((j - 9) * (j - 1)) + 5) / (2 * (j - 1)))

    def _inverse_cdf_f(self, j: NDArray) -> NDArray:
        """Inverse distribution function of subsequent random variables, which have law F."""
        # Calculated via
        #   from sympy import symbols, Eq, solve, simplify
        #   i, j = symbols("i j")
        #   cdf = Eq(j, 1 - 6 / ((i + 1) * (i + 2) * (i + 3)))
        #   simplify(solve(cdf, i)[2])
        # then further simplified manually.
        t = np.sqrt(-3 + 729 / (j - 1) ** 2)
        return np.ceil(
            -2
            - np.cbrt(t / 9 + 3 / (j - 1))
            - np.cbrt((j - 1) / (3 * t * (j - 1) + 81)),
        )

    def generate(
        self,
        N: int,
        seed: int | None = None,
    ) -> NDArray:
        """Generate a sequence of zeros and ones according to the renewal process.

        Args:
            N: length of generated sequence.
            seed: value used to initialize pseudorandom number generator.

        Returns:
            Sequence of length `N` generated by renewal process.
        """
        rng = np.random.default_rng(seed)
        uniform_sample = rng.uniform(low=0, high=0.999999, size=N)
        x_zero = self._inverse_cdf_x_zero(uniform_sample[0])
        x = np.append(x_zero, self._inverse_cdf_f(uniform_sample[1:]))
        x_cumsum = x.cumsum()
        return np.isin(np.arange(N), x_cumsum).astype(int)

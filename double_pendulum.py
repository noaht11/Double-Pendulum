from abc import ABC, abstractmethod
from typing import List, Tuple, Callable

from math import sin, cos, pi, inf, exp
import scipy.constants

###################################################################################################################################################################################
# UTILITY FUNCTIONS
###################################################################################################################################################################################

# Converts an angle in radians to the equivalent angle in radians constrained between -pi and pi, where 0 remains at angle 0
def neg_pi_to_pi(theta: float) -> float:
    modded = theta % (2*pi)
    return modded + (modded > pi) * (-2*pi)

###################################################################################################################################################################################
# DOUBLE PENDULUM DEFINITION
###################################################################################################################################################################################

# Class representing the instantaneous state of a double pendulum with at most 3 degrees of freedom:
#
#   1.  theta1  (angle between the first arm and the vertical, 0 = straight up from the pivot point)
#   2.  theta2  (angle between the second arm and the vertical, 0 = straight up from the joint)
#   3.  q       (horizontal position of the pivot point relative to an arbitrary origin)
#
# The state of the double pendulum is contained in an array of six values (in the following order):
#
#   [0]    =   theta1
#   [1]    =   theta2
#   [2]    =   q
#   [3]    =   theta1_dot   (time derivative of theta1)
#   [4]    =   theta2_dot   (time derivative of theta2)
#   [5]    =   q_dot        (time derivative of q)
#
class DoublePendulum:

    # Immutable class representing the current state of a double pendulum.
    #
    # See the DoublePendulum class description for information about each parameter.
    #
    class State:
        def __init__(self, theta1: float = 0, theta2: float = 0, q: float = 0, theta1_dot: float = 0, theta2_dot: float = 0, q_dot: float = 0):
            self.__theta1     = theta1
            self.__theta2     = theta2
            self.__q          = q
            self.__theta1_dot = theta1_dot
            self.__theta2_dot = theta2_dot
            self.__q_dot      = q_dot
        
        def theta1(self)     -> float : return self.__theta1
        def theta2(self)     -> float : return self.__theta2
        def q(self)          -> float : return self.__q
        def theta1_dot(self) -> float : return self.__theta1_dot
        def theta2_dot(self) -> float : return self.__theta2_dot
        def q_dot(self)      -> float : return self.__q_dot
        
        def __str__(self):
                return str([self.theta1(), self.theta2(), self.q(), self.theta1_dot(), self.theta2_dot(), self.q_dot()])
    
    # Immutable class representing the mechanical properties of a double pendulum.
    class Properties:
        # Initializes a new set of properties with the provided values
        #
        #   L             =   length of each arm
        #   m             =   mass of each arm
        #   d             =   moment of inertia factor such that I = 1/2 * m * d^2
        #
        def __init__(self, L: float = 1.0, m: float = 1.0, d: float = 1.0):
            self.__L = L
            self.__m = m
            self.__d = d
        
        def L(self) -> float: return self.__L
        def m(self) -> float: return self.__m
        def d(self) -> float: return self.__d

    # Initializes a new DoublePendulum with the provided properties and initial state
    #
    #   prop          =   mechanical properties of the pendulum
    #   init_state    =   initial state of the pendulum
    #
    def __init__(self, prop: Properties = Properties(), init_state: State = State()):
        self.__prop = prop
        self.__state = init_state
    
    # Returns the mechanical properties of the pendulum
    def prop(self) -> Properties:
        return self.__prop

    # Returns the current state
    def state(self) -> State:
        return self.__state

    # Sets the current state to new_state
    def set_state(self, new_state: State):
        # # Constrain the angles to between -pi and pi for easy interpretation
        # adj_state = DoublePendulum.State(
        #     neg_pi_to_pi(new_state.theta1()),
        #     neg_pi_to_pi(new_state.theta2()),
        #     new_state.q(),
        #     new_state.theta1_dot(),
        #     new_state.theta2_dot(),
        #     new_state.q_dot()
        # )
        self.__state = new_state

    # Calculates and returns the positions of the endpoints of the arms of the pendulum
    #
    # The return value is a tuple of the following form:
    #   (
    #       (pivot_x, pivot_y),
    #       (joint_x, joint_y),
    #       (end_x  , end_y  )
    #   )
    def position_ends(self) -> Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]:
        # Local copies of the state variables for convenience
        L = self.prop().L()
        theta1 = self.state().theta1()
        theta2 = self.state().theta2()
        q = self.state().q()
        
        x_1 = q + L*sin(theta1)
        y_1 = L*cos(theta1)

        x_2 = q + L*(sin(theta1) + sin(theta2))
        y_2 = L*(cos(theta1) + cos(theta2))

        return ((q, 0.0), (x_1, y_1), (x_2, y_2))
    
    # Calculates and returns the positions of the pivot point and COM (centre of mass) of each arm of the pendulum
    #
    # The return value is a tuple of the following form:
    #   (
    #       (pivot_x, pivot_y),
    #       (COM_1_x, COM_1_y),
    #       (COM_2_x, COM_2_y)
    #   )
    def position_COMs(self) -> Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]:
        # Local copies of the state variables for convenience
        L = self.prop().L()
        theta1 = self.state().theta1()
        theta2 = self.state().theta2()
        q = self.state().q()

        x_1 = q + L/2*sin(theta1)
        y_1 = L/2*cos(theta1)

        x_2 = q + L*(sin(theta1) + 1/2*sin(theta2))
        y_2 = L*(cos(theta1) + 1/2*cos(theta2))

        return ((q, 0.0), (x_1, y_1), (x_2, y_2))

    # Calculates and returns the kinetic energy of the current state of the pendulum
    def energy_kinetic(self) -> float:
        # Local copies of the state variables for convenience
        L = self.prop().L()
        m = self.prop().m()
        d = self.prop().d()
        theta1 = self.state().theta1()
        theta2 = self.state().theta2()
        q = self.state().q()
        theta1_dot = self.state().theta1_dot()
        theta2_dot = self.state().theta2_dot()
        q_dot = self.state().q_dot()

        # This is just the final formula for kinetic energy after a lot of re-arranging, so there's no good way to decompose it
        T = 1/2*m * (2*q_dot**2   +   q_dot*L*(3*cos(theta1)*theta1_dot + cos(theta2)*theta2_dot)   +   L**2*(1/4*(5*theta1_dot**2 + theta2_dot**2) + theta1_dot*theta2_dot*cos(theta1 - theta2))   +   d**2*(theta1_dot**2 + theta2_dot**2))

        return T

###################################################################################################################################################################################
# IMPLEMENTATION BASE CLASSES
###################################################################################################################################################################################

# Abstract Base Class for representing a potential
class Potential(ABC):

    # Returns the value of the potential given the current state of the pendulum
    # NOTE: Although the state includes the time derivatives of each coordinate,
    #       the potential should be purely a function of the coordinates
    #
    # The potential should be representable as a sum of functions of each individual coordinate
    # The return value of this method should be the value of each of those functions in a vector as follows:
    #    _           _
    #   |  U(theta1)  |
    #   |  U(theta2)  |
    #   |_ U(q)      _|
    #
    # where U_total = U(theta1), U(theta2), U(q)
    #
    @abstractmethod
    def U(self, t: float, state: DoublePendulum.State, prop: DoublePendulum.Properties) -> List[float]:
        pass
    
    # Returns the value of the derivative of the potential with respect to each coordinate
    # given the current state of the pendulum
    # 
    # The return value should be a vector in the following form:
    #    _                    _
    #   |  dU(theta1)/dtheta1  |
    #   |  dU(theta2)/dtheta2  |
    #   |_ dU(q)/dq           _|
    #
    @abstractmethod
    def dU_dcoord(self, t: float, state: DoublePendulum.State, prop: DoublePendulum.Properties) -> float:
        pass

# Abstract Base Class for implementations of the behavior of a DoublePendulum
#
# The behavior of a double pendulum is defined by a differential equation of the following form:
#
#   dy/dt = f(t, y)
#
# where y is a vector of values describing the current state of the pendulum
#
# (y does not have to have the exact same data the same as DoublePendulum.State but you must be able to
#  translate from one to the other, i.e. they must effectively contain the same information)
#
class DoublePendulumBehavior(ABC):
    # Converts a DoublePendulum.State to the internal state representation (y) that is used in the differential equation
    # defining this behavior
    #
    # The return value of this method will be passed to dstate_dt
    @abstractmethod
    def state_to_y(self, t: float, state: DoublePendulum.State, prop: DoublePendulum.Properties) -> List[float]:
        pass
    
    # Converts an internal state representation (y) back into a DoublePendulum.State
    @abstractmethod
    def y_to_state(self, t: float, y: List[float], prop: DoublePendulum.Properties) -> DoublePendulum.State:
        pass
    
    # Core mathematical description of this behavior
    #
    # This is the function f(t, y) mentioned in the DoublePendulumBehavior class description:
    # 
    #   Given an internal state representation y, computes the time derivative, dy/dt
    #
    @abstractmethod
    def dy_dt(self, t: float, y: List[float], prop: DoublePendulum.Properties) -> List[float]:
        pass
    
    # Returns the potential energy, a pendulum in the given state and with the given properties would have
    # according to this behavior
    @abstractmethod
    def energy_potential(self, t: float, state: DoublePendulum.State, prop: DoublePendulum.Properties) -> float:
        pass

# Abstract Base Class for implementing numerical methods to solve the time evolution of a Double Pendulum
class TimeEvolver(ABC):

    # Updates the state of the pendulum to it's new state at time t + dt according to the provided behavior
    def evolve(self, pendulum : DoublePendulum, behavior: DoublePendulumBehavior, t: float, dt: float):
        # Convert the current state to y vector (at time t)
        state_0 = pendulum.state()
        y_0 = behavior.state_to_y(t, state_0, pendulum.prop())

        # Solve the ODE
        y_1 = self.solve_ode(t, dt, behavior.dy_dt, y_0, pendulum.prop())

        # Convert resulting y vector back to state (at time d + dt now)
        state_1 = behavior.y_to_state(t + dt, y_1, pendulum.prop())

        # Update the pendulum
        pendulum.set_state(state_1)
    
    # Solves the ODE defined by:
    #
    #   dy/dt = dy_dt(y)
    # 
    # with initial condition:
    #
    #   y(t_0) = y_0
    #
    # to find:
    #
    #   y(t) between t_0 and t_0 + dt
    #
    # NOTE: the absolute time t_0 is not accurate nor meaningful here so dy/dt should not depend on t_0
    @abstractmethod
    def solve_ode(self, t_0: float, dt: float, dy_dt: Callable[[float, List[float], DoublePendulum.Properties], List[float]], y_0: List[float], prop: DoublePendulum.Properties):
        pass

###################################################################################################################################################################################
# TIME EVOLVER IMPLEMENTATIONS
###################################################################################################################################################################################

import numpy as np
from scipy.integrate import odeint

# TimeEvolver implementation that uses scipy.integrate.odeint to solve ODEs
class ODEINTTimeEvolver(TimeEvolver):
    def solve_ode(self, t_0: float, dt: float, dy_dt: Callable[[float, List[float], DoublePendulum.Properties], List[float]], y_0: List[float], prop: DoublePendulum.Properties):
        return odeint(dy_dt, y_0, [t_0, t_0 + dt], args = (prop,), tfirst = True)[1]

###################################################################################################################################################################################
# POTENTIALS
###################################################################################################################################################################################

# A potential that is the sum of two other potentials
class SumPotential(Potential):

    def __init__(self, potentialA: Potential, potentialB: Potential, subtract: bool = False):
        self.__potentialA = potentialA
        self.__potentialB = potentialB
        self.__subtract = subtract
    
    def op(self):
        return (-1 if self.__subtract else 1)

    def U(self, t: float, state: DoublePendulum.State, prop: DoublePendulum.Properties) -> List[float]:
        return np.array(self.__potentialA.U(t, state, prop)) + self.op() * np.array(self.__potentialB.U(t, state, prop))
    
    def dU_dcoord(self, t: float, state: DoublePendulum.State, prop: DoublePendulum.Properties) -> List[float]:
        return np.array(self.__potentialA.dU_dcoord(t, state, prop)) + self.op() * np.array(self.__potentialB.dU_dcoord(t, state, prop))

# A base implementation of Potential that adds support for using the + and - operators
#
# All custom defined potentials should inherit from BasePotential instead of Potential,
# so that they support these operators
#
class BasePotential(Potential):

    def __add__(self, other):
        return SumPotential(self, other, subtract = False)
    
    def __sub__(self, other):
        return SumPotential(self, other, subtract = True)

# A potential that is zero everywhere
class ZeroPotential(BasePotential):

    def U(self, t: float, state: DoublePendulum.State, prop: DoublePendulum.Properties) -> List[float]:
        return [0,0,0]
    
    def dU_dcoord(self, t: float, state: DoublePendulum.State, prop: DoublePendulum.Properties) -> List[float]:
        return [0,0,0]

# The potential energy due to gravity where 0 is at the height of the pivot point (q)
class GravitationalPotential(BasePotential):
    # Fundamental constants:
    g = scipy.constants.g

    def U(self, t: float, state: DoublePendulum.State, prop: DoublePendulum.Properties) -> List[float]:
        g = GravitationalPotential.g

        # Local copies of the state variables for convenience
        L = prop.L()
        m = prop.m()
        theta1 = state.theta1()
        theta2 = state.theta2()
        
        # Gravitational potential energy for each coordinate:
        U_theta1 = 3/2*m*g*L*cos(theta1)
        U_theta2 = 1/2*m*g*L*cos(theta2)
        U_q = 0 # By definition (the pivot point is potential 0)

        return [U_theta1, U_theta2, U_q]
    
    def dU_dcoord(self, t: float, state: DoublePendulum.State, prop: DoublePendulum.Properties) -> List[float]:
        g = GravitationalPotential.g

        # Local copies of the state variables for convenience
        L = prop.L()
        m = prop.m()
        theta1 = state.theta1()
        theta2 = state.theta2()

        dU_dtheta1 = -3/2*m*g*L*sin(theta1)
        dU_dtheta2 = -1/2*m*g*L*sin(theta2)
        dU_dq = 0 # q has no effect on gravitational potential

        return [dU_dtheta1, dU_dtheta2, dU_dq]

# A harmonic oscillator potential where:
#
#   U(coord) = 1/2 * coord_k * (coord - coord_eq)^2
#
class HarmonicOscillatorPotential(BasePotential):

    def __init__(self, theta1_k: float = 0, theta1_eq: float = 0, theta2_k: float = 0, theta2_eq: float = 0, q_k: float = 0, q_eq: float = 0):
        self.__theta1_k  = theta1_k
        self.__theta1_eq = theta1_eq
        self.__theta2_k  = theta2_k
        self.__theta2_eq = theta2_eq
        self.__q_k       = q_k
        self.__q_eq      = q_eq

    def U(self, t: float, state: DoublePendulum.State, prop: DoublePendulum.Properties) -> List[float]:
        return [
            1/2 * self.__theta1_k * (state.theta1() - self.__theta1_eq)**2,
            1/2 * self.__theta2_k * (state.theta2() - self.__theta2_eq)**2,
            1/2 * self.__q_k      * (state.q()      - self.__q_eq     )**2
        ]
    
    def dU_dcoord(self, t: float, state: DoublePendulum.State, prop: DoublePendulum.Properties) -> List[float]:
        return [
            self.__theta1_k * (state.theta1() - self.__theta1_eq),
            self.__theta2_k * (state.theta2() - self.__theta2_eq),
            self.__q_k      * (state.q()      - self.__q_eq     )
        ]

FIXED_APPROX_COEFF = 1E2

# A potential that approximately fixes q (the pivot point) in place
#
# This is accomplished by created an extremely strong harmonic oscillator potential
# with a stable equilibrium at q = q_eq such that q would need absurd amounts of
# kinetic energy to leave that equilibrium position
#
def FixedQPotential(q_eq: float = 0):
    return HarmonicOscillatorPotential(q_k = FIXED_APPROX_COEFF, q_eq = q_eq)

# A potential that approximately fixes theta1 = theta2, so that the pendulum behaves like a single pendulum
#
# This is accomplished by created an extremely strong harmonic oscillator potential
# with a stable equilibrium at theta1 = theta2 such that you would need absurd amounts of
# kinetic energy to leave that equilibrium position
#
class SinglePendulumPotential(BasePotential):

    def U(self, t: float, state: DoublePendulum.State, prop: DoublePendulum.Properties) -> List[float]:
        return [
            1/2 * FIXED_APPROX_COEFF * (state.theta1() - state.theta2())**2,
            1/2 * FIXED_APPROX_COEFF * (state.theta2() - state.theta1())**2,
            0
        ]
    
    def dU_dcoord(self, t: float, state: DoublePendulum.State, prop: DoublePendulum.Properties) -> List[float]:
        return [
            FIXED_APPROX_COEFF * (state.theta1() - state.theta2()),
            FIXED_APPROX_COEFF * (state.theta2() - state.theta1()),
            0
        ]

###################################################################################################################################################################################
# BEHAVIOR IMPLEMENTATIONS
###################################################################################################################################################################################

# Base implementation for a DoublePendulumBehavior that provides a convenient way to behave at least according to gravity
class BaseDoublePendulumBehavior(DoublePendulumBehavior):

    # Internal static (class) reference to an instance of GravitationalPotential so we don't have to keep instantiating one
    __gravity: Potential = GravitationalPotential()

    # Returns an instance of a gravitational potential
    def gravity(self) -> Potential:
        return BaseDoublePendulumBehavior.__gravity
    
    # Implementation of energy_potential that just returns the potential energy due to gravity
    def energy_potential(self, t: float, state: DoublePendulum.State, prop: DoublePendulum.Properties):
        return np.sum(self.gravity().U(t, state, prop))

# Implementation of DoublePendulumBehavior that acts as a regular double pendulum with a pivot point free to move in the horizontal direction,
# and an optional forcing potential
#
#   => theta1 and theta2 are independent
#   => theta1_dot and theta2_dot are independent
#   => q is not noecessarily 0
#   => q_dot is not necessarily 0
#
# The double pendulum is easiest to solve in the following state space (y vector):
#   [
#     theta1,
#     theta2,
#     q,
#     p_theta1,
#     p_theta2,
#     p_q
#   ]
#
#   where p_theta1 is the generalized momentum for theta1 (obtained from the Lagrangian)
#         p_theta2 is the generalized momentum for theta2 (obtained from the Lagrangian)
#         p_q      is the generalized momentum for q      (obtained from the Lagrangian)
#
# See https://en.wikipedia.org/wiki/Double_pendulum for more information
#
class GeneralDoublePendulumBehavior(BaseDoublePendulumBehavior):
    
    # Instantiates a GeneralDoublePendulumBehavior with the provided (optional) forcing potential)
    def __init__(self, forcing_potential: Potential = ZeroPotential()):
        self.__forcing_potential = forcing_potential

    # There is a set of 3 linear equations (3 knowns, 3 unknowns) that relate the following four quantities:
    #
    #   theta1_dot
    #   theta2_dot
    #   q_dot
    #   p_theta1
    #   p_theta2
    #   p_q
    #
    # The coefficients for these equations are functions of theta1, theta2, L and d and are returned by this method
    # in the form of a 3x3 matrix, that satsifies the following equation
    #  _          _   _            _         _          _
    # |  A1 A2 A3  | |  theta1_dot  |   =   |  p_theta1  |
    # |  B1 B2 B3  | |  theta2_dot  |       |  p_theta2  |
    # |_ C1 C2 C3 _| |_ q_dot      _|       |_ p_q      _|
    #
    def _coord_dot_p_coord_matrix(self, theta1: float, theta2: float, L: float, m: float, d: float) -> List[List[float]]:
        return np.array([
            [ L**2*5/2 + 2*d**2         , L**2*cos(theta1 - theta2) , 3*L*cos(theta1) ],
            [ L**2*cos(theta1 - theta2) , L**2*1/2 + 2*d**2         , L*cos(theta2)   ],
            [ 3*L*cos(theta1)           , L*cos(theta2)             , 4               ]
        ]) * 1/2*m

    def _p_coord_coord_dot_matrix(self, theta1: float, theta2:float, L: float, m: float, d: float) -> List[List[float]]:
        return np.linalg.inv(self._coord_dot_p_coord_matrix(theta1, theta2, L, m, d))

    # Transforms a vector of
    #    _            _ 
    #   |  theta1_dot  |
    #   |  theta2_dot  |
    #   |_ q_dot      _|
    #
    # to a vector
    #    _          _
    #   |  p_theta1  |
    #   |  p_theta2  |
    #   |_ p_q      _|
    #
    # using theta1, theta2, L and d
    #
    def _coord_dot_to_p_coord(self, coord_dot: List[float], theta1: float, theta2: float, L: float, m: float, d: float) -> List[float]:
        matrix = self._coord_dot_p_coord_matrix(theta1, theta2, L, m, d)
        return np.matmul(matrix, coord_dot)

    # Transforms a vector of
    #    _          _ 
    #   |  p_theta1  |
    #   |  p_theta2  |
    #   |_ p_q      _|
    #
    # to a vector
    #    _            _
    #   |  theta1_dot  |
    #   |  theta2_dot  |
    #   |_ q_dot      _|
    #
    # using theta1, theta2, L and d
    #
    def _p_coord_to_coord_dot(self, p_coord: List[float], theta1: float, theta2: float, L: float, m: float, d: float) -> List[float]:
        matrix = self._p_coord_coord_dot_matrix(theta1, theta2, L, m, d)
        return np.matmul(matrix, p_coord)

    # Calculates p_theta1_dot given the parameters of the currents state and the potential
    def _p_theta1_dot(self, theta1: float, theta2: float, theta1_dot: float, theta2_dot: float, q_dot: float, potential_term: float, L: float, m: float) -> float:
        return 1/2*m * (-3*q_dot*L*theta1_dot*sin(theta1) - L**2*theta1_dot*theta2_dot*sin(theta1 - theta2)) - potential_term

    # Calculates p_theta2_dot given the parameters of the currents state and the potential
    def _p_theta2_dot(self, theta1: float, theta2: float, theta1_dot: float, theta2_dot: float, q_dot: float, potential_term: float, L: float, m: float) -> float:
        return 1/2*m * (-1*q_dot*L*theta2_dot*sin(theta2) + L**2*theta1_dot*theta2_dot*sin(theta1 - theta2)) - potential_term

    def state_to_y(self, t: float, state: DoublePendulum.State, prop: DoublePendulum.Properties) -> List[float]:
        # Construct y vector
        L = prop.L()
        m = prop.m()
        d = prop.d()

        theta1 = state.theta1()
        theta2 = state.theta2()
        q      = state.q()
        theta1_dot = state.theta1_dot()
        theta2_dot = state.theta2_dot()
        q_dot      = state.q_dot()

        p_coord = self._coord_dot_to_p_coord([theta1_dot, theta2_dot, q_dot], theta1, theta2, L, m, d)

        return [theta1, theta2, q, p_coord[0], p_coord[1], p_coord[2]]
    
    def y_to_state(self, t: float, y: List[float], prop: DoublePendulum.Properties) -> DoublePendulum.State:
        L = prop.L()
        m = prop.m()
        d = prop.d()

        theta1 = y[0]
        theta2 = y[1]
        q      = y[2]
        p_theta1 = y[3]
        p_theta2 = y[4]
        p_q      = y[5]

        coord_dot = self._p_coord_to_coord_dot([p_theta1, p_theta2, p_q], theta1, theta2, L, m, d)

        return DoublePendulum.State(
            theta1     = theta1,
            theta2     = theta2,
            q          = q,
            theta1_dot = coord_dot[0],
            theta2_dot = coord_dot[1],
            q_dot      = coord_dot[2]
        )
    
    def dy_dt(self, t: float, y: List[float], prop: DoublePendulum.Properties) -> List[float]:
        L = prop.L()
        m = prop.m()
        d = prop.d()

        # Local variables for the y vector elements
        theta1 = y[0]
        theta2 = y[1]
        q      = y[2]
        p_theta1 = y[3]
        p_theta2 = y[4]
        p_q      = y[5]

        # Calculate the time derivatives of each coordinate from the generalized momenta
        coord_dot = self._p_coord_to_coord_dot([p_theta1, p_theta2, p_q], theta1, theta2, L, m, d)
        theta1_dot = coord_dot[0]
        theta2_dot = coord_dot[1]
        q_dot      = coord_dot[2]

        # Store everything is a state instance for passing to functions
        state = DoublePendulum.State(theta1, theta2, q, theta1_dot, theta2_dot, q_dot)

        # Take into account potential due to gravity and our forcing potential
        gravity_terms = self.gravity().dU_dcoord(t, state, prop)
        forcing_terms = self.__forcing_potential.dU_dcoord(t, state, prop)

        # Calculate the time derivatives of the generalized momenta
        p_theta1_dot = self._p_theta1_dot(theta1, theta2, theta1_dot, theta2_dot, q_dot, gravity_terms[0] + forcing_terms[0], L, m)
        p_theta2_dot = self._p_theta2_dot(theta1, theta2, theta1_dot, theta2_dot, q_dot, gravity_terms[1] + forcing_terms[1], L, m)
        p_q_dot      = 0 - (gravity_terms[2] + forcing_terms[2])

        return [theta1_dot, theta2_dot, q_dot, p_theta1_dot, p_theta2_dot, p_q_dot]
    
    def energy_potential(self, t: float, state: DoublePendulum.State, prop: DoublePendulum.Properties):
        return np.sum(self.gravity().U(t, state, prop) + self.__forcing_potential.U(t, state, prop))

# Abstract Base Class for a forcing function on the coordinate q
#
# A forcing function is fully defined by its value as a function of time
# and its derivative as a function of time
class QForcingFunction(ABC):

    @abstractmethod
    def q(self, t: float) -> float:
        pass
    
    @abstractmethod
    def dq_dt(self, t: float) -> float:
        pass

# A forcing function that holds q fixed at a given point (by default, 0)
class FixedQForcingFunction(QForcingFunction):
    
    def __init__(self, fixed_q: float = 0):
        self.__fixed_q = fixed_q

    def q(self, t: float) -> float: return self.__fixed_q
    def dq_dt(self, t: float) -> float: return 0

# A sinusoidal forcing function with a configurable amplitude, frequency and phase
class SinusoidalForcing(QForcingFunction):
    
    def __init__(self, amplitude: float = 1, frequency: float = 1, phase = 0, damping = 0):
        self.__amplitude = amplitude
        self.__frequency = frequency
        self.__phase = phase
        self.__damping = damping

    def q(self, t: float) -> float: return self.__amplitude * exp(-1*self.__damping * t) * sin(2*pi*self.__frequency*t - self.__phase)
    def dq_dt(self, t: float) -> float: return self.__amplitude * exp(-1*self.__damping * t) * (-1*self.__damping * sin(2*pi*self.__frequency*t - self.__phase) +  2*pi*self.__frequency * cos(2*pi*self.__frequency*t - self.__phase))

import sympy as sym
from sympy import symbols, lambdify, diff
sym.init_printing()

class SymbolicForcing(QForcingFunction):

    def __init__(self, q_sym):
        t = symbols('t')
        self.__q_sym = lambdify(t, q_sym)
        self.__dq_dt_sym = lambdify(t, diff(q_sym, t))
    
    def q(self, t: float) -> float: return self.__q_sym(t)
    def dq_dt(self, t: float) -> float: return self.__dq_dt_sym(t)

def SymbolicSinusoidalForcing(A = 1, w = 1, phi = 0, k = 0):
    t = symbols('t')
    expr = A * sym.exp(-1*k * t) * sym.sin(w*t - phi)
    return expr

# Implementation of DoublePendulumBehavior that forces q and q_dot according to a given function
# instead of solving for them.
#
# This class extends GeneralDoublePendulumBehavior, but overrides the core behavior methods to force q and q_dot.
#
# It also supports a forcing_potential in addition to the forcing function on q
#
class ForcedQDoublePendulumBehavior(GeneralDoublePendulumBehavior):
    
    def __init__(self, forcing_function: QForcingFunction = FixedQForcingFunction(), forcing_potential: Potential = ZeroPotential()):
        super().__init__(forcing_potential = forcing_potential)
        self.__ff = forcing_function
        self.__forcing_potential = forcing_potential

    # Calculates p_theta1 and p_theta2, given theta1, theta2, q_dot and pendulum properties
    #
    # This function uses the matrix coefficients provided by the super class, but re-organizes them to use a given q_dot instead of solving for it
    #
    # The new system of equations can be represented by the following matrix equation (there is no longer an equation for p_q)
    #  _          _   _            _         _          _
    # |  A1 A2 A3  | |  theta1_dot  |   =   |  p_theta1  |
    # |_ B1 B2 B3 _| |  theta2_dot  |       |_ p_theta2 _|
    #                |_ q_dot      _|
    #
    # To invert this system and solve for theta1_dot and theta2_dot we have the following matrix equation:
    #  _     _   _            _         _          _         _          _
    # | A1 A2 | |  theta1_dot  |   =   |  p_theta1  |   -   |  A3*q_dot  |
    # |_B1 B2_| |_ theta2_dot _|       |_ p_theta2 _|       |_ B3*q_dot _|
    #
    # Therefore theta1_dot and theta2_dot can be obtained by multiplying the RHS by the inverse of the 2x2 matrix
    #
    def _p_theta_theta_dot(self, p_theta: List[float], theta1: float, theta2: float, q_dot: float, L: float, m: float, d: float) -> List[float]:
        # Get the original matrix from the superclass
        matrix = self._coord_dot_p_coord_matrix(theta1, theta2, L, m, d)

        # Calculate the RHS of the matrix equation using the top-right and middle-right coefficients from the matrix
        p_theta_adj = p_theta - q_dot * matrix[0:2, 2]

        # Extract the 2x2 top-left sub-matrix (i.e. the coefficients multiplying only theta1_dot and theta2_dot)
        matrix_adj = matrix[0:2, 0:2]

        # Invert the matrix and multiply by the RHS to solve for theta1_dot and theta2_dot
        theta_dot = np.matmul(np.linalg.inv(matrix_adj), p_theta_adj)
        return theta_dot

    def state_to_y(self, t: float, state: DoublePendulum.State, prop: DoublePendulum.Properties) -> List[float]:
        # Construct y vector
        L = prop.L()
        m = prop.m()
        d = prop.d()

        theta1 = state.theta1()
        theta2 = state.theta2()
        q      = state.q()
        theta1_dot = state.theta1_dot()
        theta2_dot = state.theta2_dot()
        q_dot      = state.q_dot()

        # Enforce that the state of q and q_dot always matches the forcing function values
        assert(q == self.__ff.q(t))
        assert(q_dot == self.__ff.dq_dt(t))

        p_coord = self._coord_dot_to_p_coord([theta1_dot, theta2_dot, q_dot], theta1, theta2, L, m, d)

        # The y-vector representation no longer has q and p_q_dot since they are not part of the differential equation when they are forced
        return [theta1, theta2, p_coord[0], p_coord[1]]
    
    def y_to_state(self, t: float, y: List[float], prop: DoublePendulum.Properties) -> DoublePendulum.State:
        L = prop.L()
        m = prop.m()
        d = prop.d()

        theta1 = y[0]
        theta2 = y[1]
        p_theta1 = y[2]
        p_theta2 = y[3]

        # Get q and q_dot from the forcing function
        q = self.__ff.q(t)
        q_dot = self.__ff.dq_dt(t)

        # Calculate theta1_dot and theta2_dot from p_theta1_dot, p_theta2_dot and q_dot
        theta_dot = self._p_theta_theta_dot([p_theta1, p_theta2], theta1, theta2, q_dot, L, m, d)
        
        return DoublePendulum.State(
            theta1     = theta1,
            theta2     = theta2,
            q          = q,
            theta1_dot = theta_dot[0],
            theta2_dot = theta_dot[1],
            q_dot      = q_dot
        )
        
    def dy_dt(self, t: float, y: List[float], prop: DoublePendulum.Properties) -> List[float]:
        L = prop.L()
        m = prop.m()
        d = prop.d()

        theta1 = y[0]
        theta2 = y[1]
        p_theta1 = y[2]
        p_theta2 = y[3]

        # Get q and q_dot from the forcing function
        q = self.__ff.q(t)
        q_dot = self.__ff.dq_dt(t)

        # Calculate theta1_dot and theta2_dot from p_theta1_dot, p_theta2_dot and q_dot
        theta_dot = self._p_theta_theta_dot([p_theta1, p_theta2], theta1, theta2, q_dot, L, m, d)
        theta1_dot = theta_dot[0]
        theta2_dot = theta_dot[1]

        # Store everything is a state instance for passing to functions
        state = DoublePendulum.State(theta1, theta2, q, theta1_dot, theta2_dot, q_dot)

        # Take into account potential due to gravity and our forcing potential
        gravity_terms = self.gravity().dU_dcoord(t, state, prop)
        forcing_terms = self.__forcing_potential.dU_dcoord(t, state, prop)

        # Calculate the time derivatives of the generalized momenta
        p_theta1_dot = self._p_theta1_dot(theta1, theta2, theta1_dot, theta2_dot, q_dot, gravity_terms[0] + forcing_terms[0], L, m)
        p_theta2_dot = self._p_theta2_dot(theta1, theta2, theta1_dot, theta2_dot, q_dot, gravity_terms[1] + forcing_terms[1], L, m)

        return [theta1_dot, theta2_dot, p_theta1_dot, p_theta2_dot]

###################################################################################################################################################################################
# PENDULATION SIMULATION
###################################################################################################################################################################################

# Class that manages the evolution of the double pendulum over time
class DoublePendulumSimulation:
    def __init__(self, pendulum: DoublePendulum, behavior: DoublePendulumBehavior, time_evolver: TimeEvolver):
        self.__pendulum = pendulum
        self.__behavior = behavior
        self.__time_evolver = time_evolver

        self.init_state = self.__pendulum.state()
        self.__elapsed_time = 0

        self.__t = np.array(0)
        self.__q = np.array(pendulum.state().q())

    def pendulum(self) -> DoublePendulum: return self.__pendulum
    def behavior(self) -> DoublePendulumBehavior: return self.__behavior
    def time_evolver(self) -> TimeEvolver: return self.__time_evolver
    
    def elapsed_time(self) -> float: return self.__elapsed_time

    # Calculates the current energy (potential and kinetic) of the pendulum
    #
    # Return value is a tuple of the form: (potential, kinetic)
    #
    def energy(self) -> Tuple[float, float]:
        potential = self.__behavior.energy_potential(self.__elapsed_time, self.__pendulum.state(), self.__pendulum.prop())
        kinetic = self.__pendulum.energy_kinetic()
        return (potential, kinetic)

    # Resets the pendulum to its initial state and returns to time 0
    def reset(self):
        self.__pendulum.set_state(self.init_state)
        self.__elapsed_time = 0

    # Progresses the simulation through a time step, dt
    def step(self, dt: float):
        # Calculate next state
        self.time_evolver().evolve(self.pendulum(), self.behavior(), self.__elapsed_time, dt)
        # Update elapsed time
        self.__elapsed_time += dt

        # Update graph arrays
        # self.__t = np.append(self.__t, self.__elapsed_time)
        # self.__q = np.append(self.__q, self.pendulum().state().q())

    # Progresses the simulation up to absolute time, t_final, in steps of dt
    def step_until(self, dt: float, t_final: float):
        while (self.elapsed_time() < t_final):
            self.step(dt)
    
    # Progresses the simulation through an amount of time, delta_t, in steps of dt
    def step_for(self, dt: float, delta_t: float):
        local_elapsed_time = 0.0
        while (local_elapsed_time < delta_t):
            self.step(dt)
            local_elapsed_time += dt

###################################################################################################################################################################################
# ANIMATORS
###################################################################################################################################################################################

from time import time

import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Animates a DoublePendulumSimulation
class DoublePendulumAnimator:
    def __init__(self, simulation: DoublePendulumSimulation):
        self.__simulation = simulation

    # Performs all the setup necessary before running an animation
    #
    # This MUST be called before calling run()
    #
    def init(self):
        # Creat the figure
        self.fig = plt.figure(figsize=(8, 8))

        # Define how much larger the plot will be than the size of the pendulum
        scale_margin_factor_x = 3
        scale_margin_factor_y = 3
        L = self.__simulation.pendulum().prop().L()
        scale_x = (-1 * scale_margin_factor_x * L, scale_margin_factor_x * L)
        scale_y = (-1 * scale_margin_factor_y * L, scale_margin_factor_y * L)

        # Create the subplot
        self.ax_main = self.fig.add_subplot(111, aspect='equal', autoscale_on=False, xlim=scale_x, ylim=scale_y)
        self.ax_main.set_axis_off() # Hide the axes

        # The plot that will show the lines of the pendulum
        self.line_main, = self.ax_main.plot([], [], '-', lw=4)

        # A horizontal line at the pivot point of the pendulum
        num_points = 50
        self.ax_main.plot(np.linspace(scale_x[0], scale_x[1], num_points), np.zeros((num_points, 1)))

        # Text indicators
        self.time_text_main = self.ax_main.text(0.02, 0.95, '', transform=self.ax_main.transAxes)
        self.energy_text = self.ax_main.text(0.02, 0.85, '', transform=self.ax_main.transAxes)

        self.__reset()

    # Resets the simulation to its initial conditions
    # Resets all data and labels to default values
    def __reset(self):
        self.__simulation.reset()

        self.line_main.set_data([],[])
        self.time_text_main.set_text('')
        self.energy_text.set_text('')

        # Required for matplotlib to update
        return self.line_main, self.time_text_main, self.energy_text

    # Internal function that performs a single animation step
    def __animate(self, i: int, dt: float, draw_dt: float):
        # Simulate next step
        self.__simulation.step_for(dt, draw_dt)

        # Update pendulum position plot
        ((x_0, y_0), (x_1, y_1), (x_2, y_2)) = self.__simulation.pendulum().position_ends()
        x = [x_0, x_1, x_2]
        y = [y_0, y_1, y_2]
        self.line_main.set_data(x, y)

        # Update elapsed time text
        self.time_text_main.set_text('time = %.1f s' % self.__simulation.elapsed_time())

        # Update energy text
        (potential, kinetic) = self.__simulation.energy()
        total_energy = potential + kinetic
        self.energy_text.set_text('potential = %7.3f\nkinetic = %7.3f\ntotal = %7.3f' % (potential, kinetic, total_energy))

        # Required for matplotlib to update
        return self.line_main, self.time_text_main, self.energy_text

    # Runs and displays an animation of the pendulum
    #
    #   dt       = time step for the simulation (seconds)
    #   draw_dt  = time between animation frame updates (seconds)
    #   t_final  = time at which the simulation will stop (seconds)
    #
    def run(self, dt: float, draw_dt: float, t_final: float):
        interval = draw_dt * 1000 # interval is in milliseconds
        frames = int(t_final / dt)

        self.ani = animation.FuncAnimation(self.fig, self.__animate, fargs = (dt, draw_dt), frames=frames, interval=interval, blit=True, init_func=self.__reset, repeat=False)

        plt.show()
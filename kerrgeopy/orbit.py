from .constants import *
from .frequencies import *
from .geodesics import *
import numpy as np
import matplotlib.pyplot as plt

class Orbit:
    def __init__(self,a,p,e,x,M = None,mu=None):
        """
        Initializes an orbit with the given orbital parameters

        :param a: dimensionless angular momentum
        :type a: double
        :param p: semi-latus rectum
        :type p: double
        :param e: orbital eccentricity
        :type e: double
        :param x: cosine of the orbital inclination
        :type x: double
        :param M: mass of the black hole
        :type M: double
        :param mu: mass of the smaller body
        :type mu: double
        """
        self.a, self.p, self.e, self.x, self.M, self.mu = a, p, e, x, M, mu
        self.E, self.L, self.Q = constants_of_motion(a,p,e,x)
        self.upsilon_r, self.upsilon_theta, self.upsilon_phi, self.gamma = orbital_frequencies(a,p,e,x)

    def trajectory(self,initial_phases=(0,0,0,0)):
        """
        Computes the time, radial, polar, and azimuthal coordinates of the orbit as a function of mino time.

        :param initial_phases: tuple of initial phases for the time, radial, polar, and azimuthal coordinates, defaults to (0,0,0,0)
        :type initial_phases: tuple, optional

        :return: tuple of functions in the form (t,r,theta,phi)
        :rtype: tuple
        """
        a, p, e, x = self.a, self.p, self.e, self.x
        upsilon_r, upsilon_theta, upsilon_phi, gamma = self.upsilon_r, self.upsilon_theta, self.upsilon_phi, self.gamma
        r_phase, t_r, phi_r = radial_solutions(a,p,e,x)
        theta_phase, t_theta, phi_theta = polar_solutions(a,p,e,x)
        q_t0, q_r0, q_theta0, q_phi0 = initial_phases

        # Calculate normalization constants so that t = 0 and phi = 0 at lambda = 0 when q_t0 = 0 and q_phi0 = 0 
        C_t = t_r(q_r0)+t_theta(q_theta0)
        C_phi= phi_r(q_r0)+phi_theta(q_theta0)

        def t(mino_time):
            # equation 6
            return q_t0 + gamma*mino_time + t_r(upsilon_r*mino_time+q_r0) + t_theta(upsilon_theta*mino_time+q_theta0) - C_t
        
        def r(mino_time):
            return r_phase(upsilon_r*mino_time+q_r0)
        
        def theta(mino_time):
            return theta_phase(upsilon_theta*mino_time+q_theta0)
        
        def phi(mino_time):
            # equation 6
            return q_phi0 + upsilon_phi*mino_time + phi_r(upsilon_r*mino_time+q_r0) + phi_theta(upsilon_theta*mino_time+q_theta0) - C_phi
        
        return t, r, theta, phi

    def plot(self,lambda0=0, lambda1=20, elevation=30 ,azimuth=-60, initial_phases=(0,0,0,0), grid=True, axes=True, thickness=1):
        """
        Creates a plot of the orbit

        :param lambda0: starting mino time
        :type lambda0: double, optional
        :param lambda1: ending mino time
        :type lambda1: double, optional
        :param elevation: camera elevation angle
        :type elevation: double, optional
        :param azimuth: camera azimuthal angle
        :type azimuth: double, optional
        :param initial_phases: tuple of initial phases, defaults to (0,0,0,0)
        :type initial_phases: tuple, optional
        :param grid: if true, grid lines are shown on plot
        :type grid: bool, optional
        :param axes:if true, axes are shown on plot
        :type axes: bool, optional
        :param thickness: line thickness of the orbit
        :type thickness: double, optional

        :return: matplotlib figure and axes
        :rtype: matplotlib.figure.Figure, matplotlib.axes._subplots.AxesSubplot
        """
        lambda_range = lambda1 - lambda0
        point_density = 500
        num_pts = lambda_range*point_density
        time = np.linspace(lambda0,lambda1,num_pts)

        t, r, theta, phi = self.trajectory(initial_phases)

        # compute trajectory
        trajectory_x = r(time)*sin(theta(time))*cos(phi(time))
        trajectory_y = r(time)*sin(theta(time))*sin(phi(time))
        trajectory_z = r(time)*cos(theta(time))
        trajectory = np.column_stack((trajectory_x,trajectory_y,trajectory_z))

        # create sphere with radius equal to event horizon radius
        event_horizon = 1+sqrt(1-self.a**2)
        u = np.linspace(0, 2 * np.pi, 100)
        v = np.linspace(0, np.pi, 100)
        x_sphere = event_horizon * np.outer(np.cos(u), np.sin(v))
        y_sphere = event_horizon * np.outer(np.sin(u), np.sin(v))
        z_sphere = event_horizon * np.outer(np.ones(np.size(u)), np.cos(v))

        # convert viewing angles to radians
        elevation_rad = elevation*pi/180
        azimuth_rad = azimuth*pi/180

        # https://matplotlib.org/stable/api/toolkits/mplot3d/view_angles.html
        view_plane_normal = [cos(elevation_rad)*cos(azimuth_rad),cos(elevation_rad)*sin(azimuth_rad),sin(elevation_rad)]
        # matplotlib has no ray tracer so points behind the black hole must be filtered out manually
        # for each trajectory point compute the component normal to the viewing plane
        normal_component = np.apply_along_axis(lambda x: np.dot(view_plane_normal,x),1,trajectory)
        # compute the projection of each trajectory point onto the viewing plane
        projection = trajectory-np.transpose(normal_component*np.transpose(np.broadcast_to(view_plane_normal,(num_pts,3))))
        # find points in front of the viewing plane or outside the event horizon when projected onto the viewing plane
        condition = (np.dot(trajectory,view_plane_normal) >= 0) | (np.linalg.norm(projection,axis=1) > event_horizon)
        x_visible = trajectory_x[condition]
        y_visible = trajectory_y[condition]
        z_visible = trajectory_z[condition]

        fig = plt.figure()
        ax = fig.add_subplot(projection='3d')
        
        # plot black hole
        ax.plot_surface(x_sphere, y_sphere, z_sphere, color='black',shade=False)
        # plot orbit
        ax.scatter(x_visible,y_visible,z_visible,color="red",s=thickness)

        ax.view_init(elevation,azimuth)
        # set equal aspect ratio and orthogonal projection
        ax.set_box_aspect([np.ptp(x_visible),np.ptp(y_visible),np.ptp(z_visible)])
        # https://matplotlib.org/stable/gallery/mplot3d/projections.html
        ax.set_proj_type('ortho')

        # turn off grid and axes if specified
        if not grid: ax.grid(False)
        if not axes: ax.axis("off")

        return fig, ax
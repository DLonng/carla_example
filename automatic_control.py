#!/usr/bin/env python

# Copyright (c) 2018 Intel Labs.
# authors: German Ros (german.ros@intel.com)
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""Example of automatic vehicle control from client side."""

# 是 Python 2 中用于启用 Python 3 中的打印功能的指令。
# python2: print "Hello, World!"
# python3: print("Hello, World!") 必须要有括号
from __future__ import print_function

# This module provides a command-line argument parsing mechanism.
import argparse

# This module provides specialized container datatypes such as namedtuple, deque, Counter, etc., 
# which are extensions of the built-in container types like lists, tuples, and dictionaries
import collections
# It provides various functions and classes to manipulate dates, times, time intervals, etc.
import datetime
# This module provides a convenient way to find all files that match a specified pattern.
import glob
'''
    This module provides a flexible and powerful logging framework. 
    It allows you to output log messages to various outputs 
    such as the console, files, or network sockets. 
    It also supports different log levels and log formatting options.
'''
import logging
import math
import os
import random
'''
    This module provides support for regular expressions, 
    which are powerful tools for pattern matching and string manipulation.
'''
import re

'''
    It allows you to access command-line arguments, exit the program, 
    interact with the standard input/output streams, etc
'''
import sys

'''
该模块提供了处理弱引用的工具。
弱引用允许您保留对对象的引用，
而不会阻止它们在不再需要时被垃圾回收
'''
import weakref

try:
    import pygame
    from pygame.locals import KMOD_CTRL
    from pygame.locals import K_ESCAPE
    from pygame.locals import K_q
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

try:
    import numpy as np
except ImportError:
    raise RuntimeError(
        'cannot import numpy, make sure numpy package is installed')

# ==============================================================================
# -- Find CARLA module ---------------------------------------------------------
# ==============================================================================
try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

# ==============================================================================
# -- Add PythonAPI for release mode --------------------------------------------
# ==============================================================================
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/carla')
except IndexError:
    pass

import carla
from carla import ColorConverter as cc

from agents.navigation.behavior_agent import BehaviorAgent  # pylint: disable=import-error
from agents.navigation.roaming_agent import RoamingAgent  # pylint: disable=import-error
from agents.navigation.basic_agent import BasicAgent  # pylint: disable=import-error


# ==============================================================================
# -- Global functions ----------------------------------------------------------
# ==============================================================================


def find_weather_presets():
    """Method to find weather presets"""
    rgx = re.compile('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)')
    def name(x): return ' '.join(m.group(0) for m in rgx.finditer(x))
    presets = [x for x in dir(carla.WeatherParameters) if re.match('[A-Z].+', x)]
    return [(getattr(carla.WeatherParameters, x), name(x)) for x in presets]


def get_actor_display_name(actor, truncate=250):
    """Method to get actor display name"""
    name = ' '.join(actor.type_id.replace('_', '.').title().split('.')[1:])
    return (name[:truncate - 1] + u'\u2026') if len(name) > truncate else name


# ==============================================================================
# -- World ---------------------------------------------------------------
# ==============================================================================

'''
    class MyClass:
        def __init__(self, name):
            self.name = name

        def greet(self):
            print(f"Hello, {self.name}!")

    # Creating an instance of the class
    obj = MyClass("John")

    # Calling the class method
    obj.greet()

how to release memory?

In Python, memory management and resource deallocation are handled automatically by the garbage collector.

Python provides a special method called __del__ that you can define in a class.
However, it's generally recommended to avoid using __del__ 
because it can have unpredictable behavior and is not guaranteed to be called in all circumstances.

Instead, if your class needs to perform any cleanup or release resources, 
you can define a separate method (e.g., close, cleanup, etc.) 
and explicitly call it when you no longer need the instance

    class MyClass:
        def __init__(self):
            # Initialize resources

        def close(self):
            # Release resources or perform cleanup

    # Create an instance of the class
    obj = MyClass()

    # Use the instance

    # Explicitly call the cleanup method
    obj.close()

'''
class World(object):
    """ Class representing the surrounding environment """

    def __init__(self, carla_world, hud, args):
        """Constructor method"""
        self.world = carla_world
        try:
            self.map = self.world.get_map()
        except RuntimeError as error:
            print('RuntimeError: {}'.format(error))
            print('  The server could not send the OpenDRIVE (.xodr) file:')
            print('  Make sure it exists, has the same name of your town, and is correct.')
            sys.exit(1)
        self.hud = hud
        self.player = None
        self.collision_sensor = None
        self.lane_invasion_sensor = None
        self.gnss_sensor = None
        self.camera_manager = None
        self._weather_presets = find_weather_presets()
        self._weather_index = 0
        self._actor_filter = args.filter
        self._gamma = args.gamma
        self.restart(args)
        # registering a callback for the on_tick event of self.world. 
        # This means that when the on_tick event occurs in self.world, 
        # the on_world_tick method of hud will be invoked.
        self.world.on_tick(hud.on_world_tick)
        self.recording_enabled = False
        self.recording_start = 0

    def restart(self, args):
        """Restart the world"""
        # Keep same camera config if the camera manager exists.
        cam_index = self.camera_manager.index if self.camera_manager is not None else 0
        cam_pos_id = self.camera_manager.transform_index if self.camera_manager is not None else 0
        # Set the seed if requested by user
        if args.seed is not None:
            random.seed(args.seed)

        # Get a random blueprint.
        blueprint = random.choice(self.world.get_blueprint_library().filter(self._actor_filter))
        blueprint.set_attribute('role_name', 'hero')
        if blueprint.has_attribute('color'):
            color = random.choice(blueprint.get_attribute('color').recommended_values)
            blueprint.set_attribute('color', color)

        # Spawn the player.
        print("Spawning the player")
        if self.player is not None:
            spawn_point = self.player.get_transform()
            spawn_point.location.z += 2.0
            spawn_point.rotation.roll = 0.0
            spawn_point.rotation.pitch = 0.0
            self.destroy()
            self.player = self.world.try_spawn_actor(blueprint, spawn_point)

        while self.player is None:
            if not self.map.get_spawn_points():
                print('There are no spawn points available in your map/town.')
                print('Please add some Vehicle Spawn Point to your UE4 scene.')
                sys.exit(1)
            spawn_points = self.map.get_spawn_points()
            spawn_point = random.choice(spawn_points) if spawn_points else carla.Transform()
            self.player = self.world.try_spawn_actor(blueprint, spawn_point)
        
        # Set up the sensors.
        self.collision_sensor = CollisionSensor(self.player, self.hud)
        self.lane_invasion_sensor = LaneInvasionSensor(self.player, self.hud)
        self.gnss_sensor = GnssSensor(self.player)
        self.camera_manager = CameraManager(self.player, self.hud, self._gamma)
        self.camera_manager.transform_index = cam_pos_id
        self.camera_manager.set_sensor(cam_index, notify=False)
        actor_type = get_actor_display_name(self.player)
        self.hud.notification(actor_type)

    def next_weather(self, reverse=False):
        """Get next weather setting"""
        self._weather_index += -1 if reverse else 1
        self._weather_index %= len(self._weather_presets)
        preset = self._weather_presets[self._weather_index]
        self.hud.notification('Weather: %s' % preset[1])
        self.player.get_world().set_weather(preset[0])

    def tick(self, clock):
        """Method for every tick"""
        self.hud.tick(self, clock)

    def render(self, display):
        """Render world"""
        self.camera_manager.render(display)
        self.hud.render(display)

    def destroy_sensors(self):
        """Destroy sensors"""
        self.camera_manager.sensor.destroy()
        self.camera_manager.sensor = None
        self.camera_manager.index = None

    def destroy(self):
        """Destroys all actors"""
        actors = [
            self.camera_manager.sensor,
            self.collision_sensor.sensor,
            self.lane_invasion_sensor.sensor,
            self.gnss_sensor.sensor,
            self.player]
        for actor in actors:
            if actor is not None:
                actor.destroy()


# ==============================================================================
# -- KeyboardControl -----------------------------------------------------------
# ==============================================================================


class KeyboardControl(object):
    def __init__(self, world):
        world.hud.notification("Press 'H' or '?' for help.", seconds=4.0)

    def parse_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            if event.type == pygame.KEYUP:
                if self._is_quit_shortcut(event.key):
                    return True

    @staticmethod
    def _is_quit_shortcut(key):
        """Shortcut for quitting"""
        return (key == K_ESCAPE) or (key == K_q and pygame.key.get_mods() & KMOD_CTRL)

# ==============================================================================
# -- HUD -----------------------------------------------------------------------
# ==============================================================================


class HUD(object):
    """Class for HUD text"""
    # self is a reference to the instance of the class being created.
    def __init__(self, width, height):
        """Constructor method"""
        self.dim = (width, height)
        font = pygame.font.Font(pygame.font.get_default_font(), 20)
        font_name = 'courier' if os.name == 'nt' else 'mono'
        fonts = [x for x in pygame.font.get_fonts() if font_name in x]
        default_font = 'ubuntumono'
        mono = default_font if default_font in fonts else fonts[0]
        
        # attempts to find the full name of a font that matches the given keyword or name.
        mono = pygame.font.match_font(mono)
        
        self._font_mono = pygame.font.Font(mono, 12 if os.name == 'nt' else 14)
        self._notifications = FadingText(font, (width, 40), (0, height - 40))
        self.help = HelpText(pygame.font.Font(mono, 24), width, height)
        self.server_fps = 0
        self.frame = 0
        self.simulation_time = 0
        self._show_info = True
        self._info_text = []
        self._server_clock = pygame.time.Clock()

    # on_world_tick() that is called at every tick of the simulation world
    def on_world_tick(self, timestamp):
        """Gets informations from the world at every tick"""
        #  updates the internal clock used to track the time in the server or simulation
        self._server_clock.tick()
        
        # update fps after _server_clokc.tick
        self.server_fps = self._server_clock.get_fps()
        
        # represents the number of frames that have passed in the simulation.
        self.frame = timestamp.frame_count
        
        # stores the elapsed time in seconds since the start of the simulation
        self.simulation_time = timestamp.elapsed_seconds

    def tick(self, world, clock):
        """HUD method for every tick"""
        self._notifications.tick(world, clock)
        if not self._show_info:
            return
        
        transform = world.player.get_transform()
        vel = world.player.get_velocity()
        control = world.player.get_control()
        
        heading = 'N' if abs(transform.rotation.yaw) < 89.5 else ''
        heading += 'S' if abs(transform.rotation.yaw) > 90.5 else ''
        heading += 'E' if 179.5 > transform.rotation.yaw > 0.5 else ''
        heading += 'W' if -0.5 > transform.rotation.yaw > -179.5 else ''
        
        colhist = world.collision_sensor.get_collision_history()
        # extracts the last 200 collision events from the collision history, 
        # starting from the self.frame value. 
        # It creates a new list called collision [self.frame - 200, self.frame]
        collision = [colhist[x + self.frame - 200] for x in range(0, 200)]
        max_col = max(1.0, max(collision))
        collision = [x / max_col for x in collision]

        # retrieves vehicle actors from the simulation world
        '''
            The ability to retrieve vehicle actors allows you to interact with, control, 
            or obtain information about the vehicles within the simulation world. 
        '''
        vehicles = world.world.get_actors().filter('vehicle.*')

        self._info_text = [
            'Server:  % 16.0f FPS' % self.server_fps,
            'Client:  % 16.0f FPS' % clock.get_fps(),
            '',
            'Vehicle: % 20s' % get_actor_display_name(world.player, truncate=20),
            'Map:     % 20s' % world.map.name,
            # represents the elapsed time in seconds.
            'Simulation time: % 12s' % datetime.timedelta(seconds=int(self.simulation_time)),
            '',
            'Speed:   % 15.0f km/h' % (3.6 * math.sqrt(vel.x**2 + vel.y**2 + vel.z**2)),
            u'Heading:% 16.0f\N{DEGREE SIGN} % 2s' % (transform.rotation.yaw, heading),
            # formats the location string with a width of 20 characters, padded with spaces if necessary.
            'Location:% 20s' % ('(% 5.1f, % 5.1f)' % (transform.location.x, transform.location.y)),
            'GNSS:% 24s' % ('(% 2.6f, % 3.6f)' % (world.gnss_sensor.lat, world.gnss_sensor.lon)),
            'Height:  % 18.0f m' % transform.location.z,
            '']
        if isinstance(control, carla.VehicleControl):
            self._info_text += [
                ('Throttle:', control.throttle, 0.0, 1.0),
                ('Steer:', control.steer, -1.0, 1.0),
                ('Brake:', control.brake, 0.0, 1.0),
                ('Reverse:', control.reverse),
                ('Hand brake:', control.hand_brake),
                ('Manual:', control.manual_gear_shift),
                'Gear:        %s' % {-1: 'R', 0: 'N'}.get(control.gear, control.gear)]
        elif isinstance(control, carla.WalkerControl):
            self._info_text += [
                ('Speed:', control.speed, 0.0, 5.556),
                ('Jump:', control.jump)]
        self._info_text += [
            '',
            'Collision:',
            collision,
            '',
            'Number of vehicles: % 8d' % len(vehicles)]

        if len(vehicles) > 1:
            self._info_text += ['Nearby vehicles:']

        def dist(l):
            return math.sqrt((l.x - transform.location.x)**2 + (l.y - transform.location.y)
                             ** 2 + (l.z - transform.location.z)**2)
        vehicles = [(dist(x.get_location()), x) for x in vehicles if x.id != world.player.id]

        for dist, vehicle in sorted(vehicles):
            if dist > 200.0:
                break
            vehicle_type = get_actor_display_name(vehicle, truncate=22)
            self._info_text.append('% 4dm %s' % (dist, vehicle_type))

    def toggle_info(self):
        """Toggle info on or off"""
        self._show_info = not self._show_info

    def notification(self, text, seconds=2.0):
        """Notification text"""
        self._notifications.set_text(text, seconds=seconds)

    def error(self, text):
        """Error text"""
        self._notifications.set_text('Error: %s' % text, (255, 0, 0))

    def render(self, display):
        """Render for HUD class"""
        if self._show_info:
            info_surface = pygame.Surface((220, self.dim[1]))
            # 100: semi-transparent, [0 fully transparent, 255 fully opaque]
            info_surface.set_alpha(100)
            '''
                draws the info_surface onto the display surface at the position (0, 0). 
                The display surface represents the main surface where the game or simulation is rendered.
            '''
            display.blit(info_surface, (0, 0))
            v_offset = 4
            bar_h_offset = 100
            bar_width = 106
            for item in self._info_text:
                if v_offset + 18 > self.dim[1]:
                    break
                if isinstance(item, list):
                    if len(item) > 1:
                        points = [(x + 8, v_offset + 8 + (1 - y) * 30) for x, y in enumerate(item)]
                        pygame.draw.lines(display, (255, 136, 0), False, points, 2)
                    item = None
                    v_offset += 18
                elif isinstance(item, tuple):
                    if isinstance(item[1], bool):
                        rect = pygame.Rect((bar_h_offset, v_offset + 8), (6, 6))
                        pygame.draw.rect(display, (255, 255, 255), rect, 0 if item[1] else 1)
                    else:
                        rect_border = pygame.Rect((bar_h_offset, v_offset + 8), (bar_width, 6))
                        pygame.draw.rect(display, (255, 255, 255), rect_border, 1)
                        fig = (item[1] - item[2]) / (item[3] - item[2])
                        if item[2] < 0.0:
                            rect = pygame.Rect(
                                (bar_h_offset + fig * (bar_width - 6), v_offset + 8), (6, 6))
                        else:
                            rect = pygame.Rect((bar_h_offset, v_offset + 8), (fig * bar_width, 6))
                        pygame.draw.rect(display, (255, 255, 255), rect)
                    item = item[0]
                if item:  # At this point has to be a str.
                    surface = self._font_mono.render(item, True, (255, 255, 255))
                    display.blit(surface, (8, v_offset))
                v_offset += 18
        self._notifications.render(display)
        self.help.render(display)

# ==============================================================================
# -- FadingText ----------------------------------------------------------------
# ==============================================================================


class FadingText(object):
    """ Class for fading text """

    def __init__(self, font, dim, pos):
        """Constructor method"""
        self.font = font
        self.dim = dim
        self.pos = pos
        self.seconds_left = 0
        self.surface = pygame.Surface(self.dim)

    def set_text(self, text, color=(255, 255, 255), seconds=2.0):
        """Set fading text"""
        text_texture = self.font.render(text, True, color)
        self.surface = pygame.Surface(self.dim)
        self.seconds_left = seconds
        # RGB alpha
        # This can be useful when you want to clear the contents 
        # of the surface or create a transparent background.
        self.surface.fill((0, 0, 0, 0))
        self.surface.blit(text_texture, (10, 11))

    def tick(self, _, clock):
        """Fading text method for every tick"""
        delta_seconds = 1e-3 * clock.get_time()
        self.seconds_left = max(0.0, self.seconds_left - delta_seconds)
        # gradual fading effect.
        self.surface.set_alpha(500.0 * self.seconds_left)

    def render(self, display):
        """Render fading text method"""
        display.blit(self.surface, self.pos)

# ==============================================================================
# -- HelpText ------------------------------------------------------------------
# ==============================================================================


class HelpText(object):
    """ Helper class for text render"""

    def __init__(self, font, width, height):
        """Constructor method"""
        lines = __doc__.split('\n')
        self.font = font
        self.dim = (680, len(lines) * 22 + 12)
        self.pos = (0.5 * width - 0.5 * self.dim[0], 0.5 * height - 0.5 * self.dim[1])
        self.seconds_left = 0
        self.surface = pygame.Surface(self.dim)
        self.surface.fill((0, 0, 0, 0))
        for i, line in enumerate(lines):
            text_texture = self.font.render(line, True, (255, 255, 255))
            self.surface.blit(text_texture, (22, i * 22))
            self._render = False
        self.surface.set_alpha(220)

    def toggle(self):
        """Toggle on or off the render help"""
        self._render = not self._render

    def render(self, display):
        """Render help text method"""
        if self._render:
            display.blit(self.surface, self.pos)

# ==============================================================================
# -- CollisionSensor -----------------------------------------------------------
# ==============================================================================


class CollisionSensor(object):
    """ Class for collision sensors"""

    def __init__(self, parent_actor, hud):
        """Constructor method"""
        self.sensor = None
        self.history = []
        self._parent = parent_actor
        self.hud = hud
        world = self._parent.get_world()
        blueprint = world.get_blueprint_library().find('sensor.other.collision')
        self.sensor = world.spawn_actor(blueprint, carla.Transform(), attach_to=self._parent)
        # We need to pass the lambda a weak reference to
        # self to avoid circular reference.
        weak_self = weakref.ref(self)
        '''
            weakref.ref(self) 创建对 self 对象的弱引用。 
            weakref.ref() 函数返回一个可调用对象，可用于间接访问引用对象。
            使用弱引用的目的是避免创建强引用，以免对象在不再需要时被垃圾回收

            通过使用弱引用并将其传递给回调函数，
            您可以确保对 self 的引用不会创建强引用循环，
            从而允许对象在必要时被垃圾回收。
        '''
        self.sensor.listen(lambda event: CollisionSensor._on_collision(weak_self, event))

    '''
        The purpose of this method is to provide a convenient way to 
        access the history of collisions and analyze the overall 
        impact or severity of collisions that occurred during the simulation.
    '''
    def get_collision_history(self):
        """Gets the history of collisions"""
        '''
            这意味着如果访问一个键但它不存在，则该值将默认为零 (0)。
        '''
        history = collections.defaultdict(int)
        for frame, intensity in self.history:
            history[frame] += intensity
        return history

    @staticmethod
    def _on_collision(weak_self, event):
        """On collision method"""
        self = weak_self()
        if not self:
            return
        actor_type = get_actor_display_name(event.other_actor)
        # %r: insert the string representation
        self.hud.notification('Collision with %r' % actor_type)
        # 表示碰撞事件的脉冲矢量。它包含在碰撞的法线方向上施加的力。
        impulse = event.normal_impulse
        # 使用欧几里得范数计算脉冲矢量的大小或强度
        intensity = math.sqrt(impulse.x ** 2 + impulse.y ** 2 + impulse.z ** 2)
        # 通过计算碰撞强度并将其存储在历史记录中，您可以跟踪模拟过程中发生的碰撞的严重程度或影响。
        self.history.append((event.frame, intensity))
        if len(self.history) > 4000:
            self.history.pop(0)

# ==============================================================================
# -- LaneInvasionSensor --------------------------------------------------------
# ==============================================================================


class LaneInvasionSensor(object):
    """Class for lane invasion sensors"""

    def __init__(self, parent_actor, hud):
        """Constructor method"""
        self.sensor = None
        self._parent = parent_actor
        self.hud = hud
        world = self._parent.get_world()
        bp = world.get_blueprint_library().find('sensor.other.lane_invasion')
        self.sensor = world.spawn_actor(bp, carla.Transform(), attach_to=self._parent)
        # We need to pass the lambda a weak reference to self to avoid circular
        # reference.
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda event: LaneInvasionSensor._on_invasion(weak_self, event))

    @staticmethod
    def _on_invasion(weak_self, event):
        """On invasion method"""
        self = weak_self()
        if not self:
            return
        lane_types = set(x.type for x in event.crossed_lane_markings)
        # The string representation is 
        # str(x): obtained by converting x to a string, 
        # split(): splitting it by spaces, 
        # [-1]: and selecting the last element.
        text = ['%r' % str(x).split()[-1] for x in lane_types]
        self.hud.notification('Crossed line %s' % ' and '.join(text))

# ==============================================================================
# -- GnssSensor --------------------------------------------------------
# ==============================================================================


class GnssSensor(object):
    """ Class for GNSS sensors"""

    def __init__(self, parent_actor):
        """Constructor method"""
        self.sensor = None
        self._parent = parent_actor
        self.lat = 0.0
        self.lon = 0.0
        world = self._parent.get_world()
        blueprint = world.get_blueprint_library().find('sensor.other.gnss')
        self.sensor = world.spawn_actor(blueprint, carla.Transform(carla.Location(x=1.0, z=2.8)),
                                        attach_to=self._parent)
        # We need to pass the lambda a weak reference to
        # self to avoid circular reference.
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda event: GnssSensor._on_gnss_event(weak_self, event))

    @staticmethod
    def _on_gnss_event(weak_self, event):
        """GNSS method"""
        self = weak_self()
        if not self:
            return
        self.lat = event.latitude
        self.lon = event.longitude

# ==============================================================================
# -- CameraManager -------------------------------------------------------------
# ==============================================================================


class CameraManager(object):
    """ Class for camera management"""

    def __init__(self, parent_actor, hud, gamma_correction):
        """Constructor method"""
        self.sensor = None
        self.surface = None
        self._parent = parent_actor
        self.hud = hud
        self.recording = False
        bound_y = 0.5 + self._parent.bounding_box.extent.y
        # an enum that represents different types of camera attachments in the CARLA simulator.
        attachment = carla.AttachmentType
        self._camera_transforms = [
            (carla.Transform(
                carla.Location(x=-5.5, z=2.5), carla.Rotation(pitch=8.0)), attachment.SpringArm),
            (carla.Transform(
                carla.Location(x=1.6, z=1.7)), attachment.Rigid),
            (carla.Transform(
                carla.Location(x=5.5, y=1.5, z=1.5)), attachment.SpringArm),
            (carla.Transform(
                carla.Location(x=-8.0, z=6.0), carla.Rotation(pitch=6.0)), attachment.SpringArm),
            (carla.Transform(
                carla.Location(x=-1, y=-bound_y, z=0.5)), attachment.Rigid)]
        self.transform_index = 1
        self.sensors = [
            ['sensor.camera.rgb', cc.Raw, 'Camera RGB'],
            ['sensor.camera.depth', cc.Raw, 'Camera Depth (Raw)'],
            ['sensor.camera.depth', cc.Depth, 'Camera Depth (Gray Scale)'],
            ['sensor.camera.depth', cc.LogarithmicDepth, 'Camera Depth (Logarithmic Gray Scale)'],
            ['sensor.camera.semantic_segmentation', cc.Raw, 'Camera Semantic Segmentation (Raw)'],
            ['sensor.camera.semantic_segmentation', cc.CityScapesPalette,
             'Camera Semantic Segmentation (CityScapes Palette)'],
            ['sensor.lidar.ray_cast', None, 'Lidar (Ray-Cast)']]
        
        world = self._parent.get_world()
        bp_library = world.get_blueprint_library()
        for item in self.sensors:
            blp = bp_library.find(item[0])
            if item[0].startswith('sensor.camera'):
                blp.set_attribute('image_size_x', str(hud.dim[0]))
                blp.set_attribute('image_size_y', str(hud.dim[1]))
                if blp.has_attribute('gamma'):
                    blp.set_attribute('gamma', str(gamma_correction))
            elif item[0].startswith('sensor.lidar'):
                blp.set_attribute('range', '50')
            item.append(blp)
        self.index = None

    def toggle_camera(self):
        """Activate a camera"""
        self.transform_index = (self.transform_index + 1) % len(self._camera_transforms)
        self.set_sensor(self.index, notify=False, force_respawn=True)

    def set_sensor(self, index, notify=True, force_respawn=False):
        """Set a sensor"""
        index = index % len(self.sensors)
        needs_respawn = True if self.index is None else (
            force_respawn or (self.sensors[index][0] != self.sensors[self.index][0]))
        if needs_respawn:
            if self.sensor is not None:
                self.sensor.destroy()
                self.surface = None
            self.sensor = self._parent.get_world().spawn_actor(
                self.sensors[index][-1],
                self._camera_transforms[self.transform_index][0],
                attach_to=self._parent,
                attachment_type=self._camera_transforms[self.transform_index][1])

            # We need to pass the lambda a weak reference to
            # self to avoid circular reference.
            weak_self = weakref.ref(self)
            self.sensor.listen(lambda image: CameraManager._parse_image(weak_self, image))
        if notify:
            self.hud.notification(self.sensors[index][2])
        self.index = index

    def next_sensor(self):
        """Get the next sensor"""
        self.set_sensor(self.index + 1)

    def toggle_recording(self):
        """Toggle recording on or off"""
        self.recording = not self.recording
        self.hud.notification('Recording %s' % ('On' if self.recording else 'Off'))

    def render(self, display):
        """Render method"""
        if self.surface is not None:
            display.blit(self.surface, (0, 0))

    @staticmethod
    def _parse_image(weak_self, image):
        self = weak_self()
        # checks if the weak reference is still valid. 
        # If the referenced object has been deleted or garbage collected, 
        # the weak reference will be None
        if not self:
            return
        # checks whether the sensor type starts with the string sensor.lidar
        if self.sensors[self.index][0].startswith('sensor.lidar'):
            # reads the raw data from the image object 
            # and converts it into a NumPy array of 32-bit floating-point values
            points = np.frombuffer(image.raw_data, dtype=np.dtype('f4'))
            # row: points.shapre[0] / 4
            # col: 4, x y z i
            points = np.reshape(points, (int(points.shape[0] / 4), 4))
            # points: N x 4(x, y, z, i)
            # [:, :2]: selects all rows(:), first two colum(:2) -> x, y
            # points: N x 2(x, y)
            # np.array: creates a new array from a sequence or iterable.
            # lidar_data: a new NumPy array containing only the first two columns of the points array.
            lidar_data = np.array(points[:, :2])
            # WxH: self.hud.dim, min(WxH) / 100.0
            # scales the lidar_data array multiplying it with a scaling factor min(WxH) / 100.0.
            lidar_data *= min(self.hud.dim) / 100.0
            # creates a tuple of two values, where each value is half of the corresponding dimension of the HUD.
            lidar_data += (0.5 * self.hud.dim[0], 0.5 * self.hud.dim[1])
            # computes the absolute values of each element in an array.
            lidar_data = np.fabs(lidar_data)  # pylint: disable=assignment-from-no-return
            # astype(): used to cast the data type of an array to a specified type.
            lidar_data = lidar_data.astype(np.int32)
            # -1: the first dimension will be automatically determined based on the size of the array, 
            #  2: the second dimension will have a size of 2
            lidar_data = np.reshape(lidar_data, (-1, 2))
            #  3: number of color channels, RGB, BGR
            lidar_img_size = (self.hud.dim[0], self.hud.dim[1], 3)
            # filled with zeros is to initialize an empty image with the specified shape
            lidar_img = np.zeros(lidar_img_size)
            # lidar_data.T: transposes the lidar_data array, swapping the rows with columns.
            # This tuple represents the pixel locations in the lidar_img array where the color will be assigned.
            lidar_img[tuple(lidar_data.T)] = (255, 255, 255)
            # a surface is an object that represents a rectangular area of pixels. 
            # It is used for drawing and displaying images
            # make_surface() function converts this array into a Pygame surface 
            # that can be displayed on the screen or used for further processing.
            self.surface = pygame.surfarray.make_surface(lidar_img)
        else:
            # converted to the specified pixel format
            # convert() method does not modify the original surface
            # it's necessary to assign the converted surface 
            # to a variable or attribute to make use of it
            image.convert(self.sensors[self.index][1])
            # converts the raw data of the image object into a NumPy array of unsigned 8-bit integers 
            array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
            # 4: RGBA
            array = np.reshape(array, (image.height, image.width, 4))
            # array: (image.height, image.width, 4)
            # array: (image.height, image.width, 3) selecting only the first three components
            array = array[:, :, :3]
            # [::-1]: reversed along the last axis, RGB -> BGR
            array = array[:, :, ::-1]
            # array.swapaxes(0, 1): HxW -> WxH
            self.surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))
        if self.recording:
            # %08d: 八位零填充整数
            image.save_to_disk('_out/%08d' % image.frame)

# ==============================================================================
# -- Game Loop ---------------------------------------------------------
# ==============================================================================


def game_loop(args):
    """ Main loop for agent"""
    # It initializes all the Pygame modules and prepares them for use
    pygame.init()
    # initializes the Pygame font module
    pygame.font.init()

    world = None
    tot_target_reached = 0
    num_min_waypoints = 21

    try:
        client = carla.Client(args.host, args.port)
        client.set_timeout(4.0)

        # provided by the Pygame library that creates a window or screen surface for displaying graphics.
        # pygame.HWSURFACE: 
        #   indicates that the display surface should be created in hardware, if available. 
        #   This flag is used for improved performance
        # pygame.DOUBLEBUF: 
        #   enables double buffering, which reduces visual artifacts by using two buffers to draw and display frames. 
        #   This is particularly useful for smoother animation
        display = pygame.display.set_mode(
            (args.width, args.height),
            pygame.HWSURFACE | pygame.DOUBLEBUF)

        hud = HUD(args.width, args.height)
        world = World(client.get_world(), hud, args)
        controller = KeyboardControl(world)

        if args.agent == "Roaming":
            agent = RoamingAgent(world.player)
        elif args.agent == "Basic":
            agent = BasicAgent(world.player)
            spawn_point = world.map.get_spawn_points()[0]
            agent.set_destination((spawn_point.location.x,
                                   spawn_point.location.y,
                                   spawn_point.location.z))
        else:
            agent = BehaviorAgent(world.player, behavior=args.behavior)

            spawn_points = world.map.get_spawn_points()
            random.shuffle(spawn_points)

            if spawn_points[0].location != agent.vehicle.get_location():
                destination = spawn_points[0].location
            else:
                destination = spawn_points[1].location

            '''
                clean=True is an optional argument that indicates 
                whether to clear any previous destination or waypoints before 
                setting the new destination. When set to True, it ensures that 
                the agent starts with a clean slate and navigates directly to the specified destination.
            '''
            agent.set_destination(agent.vehicle.get_location(), destination, clean=True)

        clock = pygame.time.Clock()

        while True:
            # helps maintain a more stable frame rate compared to the tick() method
            # more computationally expensive
            clock.tick_busy_loop(60)
            if controller.parse_events():
                return

            # As soon as the server is ready continue!
            '''
                用于在继续循环的下一次迭代之前等待世界时间前进一定的时间量。

                在CARLA模拟器中，wait_for_tick() 方法用于将模拟时间与实时时钟同步。
                它等待指定的时间量（在这种情况下为10.0秒）以使模拟时间前进。
                如果在此时间内模拟时间没有前进，意味着尚未达到期望的时间，循环将继续到下一次迭代。

                通过使用这个结构，代码确保每次循环迭代都与模拟时间同步，从而实现精确的时间控制和协调。
            '''
            if not world.world.wait_for_tick(10.0):
                continue

            if args.agent == "Roaming" or args.agent == "Basic":
                if controller.parse_events():
                    return

                '''
                    It waits for the server to be ready, then performs world updates and rendering
                '''
                # as soon as the server is ready continue!
                # Wait for the server to be ready for a maximum of 10 seconds.
                world.world.wait_for_tick(10.0)

                # Update the world state based on the clock object, which measures time intervals.
                world.tick(clock)
                # Render the world and display the rendered result on the display surface.
                world.render(display)
                # Refresh the display, showing the previously rendered result on the screen.
                pygame.display.flip()
                # Get control commands from the agent
                control = agent.run_step()
                # Set the manual gear shift flag in the control commands to False, 
                # indicating automatic gear shifting.
                control.manual_gear_shift = False
                # Apply the control commands to the player character, 
                # making it perform the corresponding actions.
                world.player.apply_control(control)
            else:
                agent.update_information(world)

                world.tick(clock)
                world.render(display)
                pygame.display.flip()

                # Set new destination when target has been reached
                if len(agent.get_local_planner().waypoints_queue) < num_min_waypoints and args.loop:
                    # Reroutes the agent by generating a new set of waypoints based on the spawn_points
                    agent.reroute(spawn_points)
                    tot_target_reached += 1
                    # The notification is shown for 4 seconds.
                    world.hud.notification("The target has been reached " +
                                           str(tot_target_reached) + " times.", seconds=4.0)

                elif len(agent.get_local_planner().waypoints_queue) == 0 and not args.loop:
                    print("Target reached, mission accomplished...")
                    break
                
                # get max speed limit
                speed_limit = world.player.get_speed_limit()
                agent.get_local_planner().set_speed(speed_limit)

                control = agent.run_step()
                world.player.apply_control(control)

    finally:
        '''
            define a block of code that will be executed after the try block, 
            regardless of whether an exception occurs or not. The finally block is typically used for performing 
            cleanup operations or executing necessary code that should always run, regardless of exceptions.
        '''
        if world is not None:
            world.destroy()

        pygame.quit()


# ==============================================================================
# -- main() --------------------------------------------------------------
# ==============================================================================


def main():
    """Main method"""

    argparser = argparse.ArgumentParser(
        description='CARLA Automatic Control Client')
    argparser.add_argument(
        # The user can use either -v or --verbose to specify this argument.
        '-v', '--verbose',
        # when this argument is provided, it sets the value of the argument to True
        action='store_true',
        # specifies the name of the attribute where the value of this argument will be stored
        # it will be stored in the args.debug attribute
        dest='debug',
        # This description will be displayed when the user runs the program with the --help option.
        help='Print debug information')
    argparser.add_argument(
        '--host',
        # 指定帮助消息中用于表示参数值的占位符名称。在这种情况下，它将在帮助消息中显示为 H。
        metavar='H',
        # sets the default value for this argument to '127.0.0.1', 
        # which is the loopback address for the local machine.
        default='127.0.0.1',
        help='IP of the host server (default: 127.0.0.1)')
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2000,
        # specifies the type of the argument value. In this case, it expects an integer value.
        type=int,
        help='TCP port to listen to (default: 2000)')
    argparser.add_argument(
        '--res',
        metavar='WIDTHxHEIGHT',
        default='1280x720',
        help='Window resolution (default: 1280x720)')
    argparser.add_argument(
        '--filter',
        metavar='PATTERN',
        default='vehicle.*',
        help='Actor filter (default: "vehicle.*")')
    argparser.add_argument(
        '--gamma',
        default=2.2,
        type=float,
        help='Gamma correction of the camera (default: 2.2)')
    argparser.add_argument(
        '-l', '--loop',
        action='store_true',
        dest='loop',
        help='Sets a new random destination upon reaching the previous one (default: False)')
    argparser.add_argument(
        '-b', '--behavior', type=str,
        choices=["cautious", "normal", "aggressive"],
        help='Choose one of the possible agent behaviors (default: normal) ',
        default='normal')
    argparser.add_argument("-a", "--agent", type=str,
                           choices=["Behavior", "Roaming", "Basic"],
                           help="select which agent to run",
                           default="Behavior")
    argparser.add_argument(
        '-s', '--seed',
        help='Set seed for repeating executions (default: None)',
        default=None,
        type=int)

    args = argparser.parse_args()

    args.width, args.height = [int(x) for x in args.res.split('x')]
    '''
        DEBUG is the lowest log level, providing detailed debugging information, 
        while INFO is a higher log level, providing general informational messages.

        displayed as "DEBUG: This is an debug message"
    '''
    log_level = logging.DEBUG if args.debug else logging.INFO

    '''
        The basicConfig() function is used to configure the logging module.
        
        level: DEBUG, INFO, WARNING, ERROR, and CRITICAL
        log_level = INFO: INFO, WARNING, ERROR, and CRITICAL
    '''
    logging.basicConfig(format='%(levelname)s: %(message)s', level=log_level)

    logging.info('listening to server %s:%s', args.host, args.port)

    print(__doc__)

    try:
        game_loop(args)

    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')


if __name__ == '__main__':
    main()

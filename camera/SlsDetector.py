############################################################################
# This file is part of LImA, a Library for Image Acquisition
#
# Copyright (C) : 2009-2011
# European Synchrotron Radiation Facility
# BP 220, Grenoble 38043
# FRANCE
#
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
############################################################################
#=============================================================================
#
# file :        SlsDetector.py
#
# description : Python source for the PSI/SlsDetector and its commands.
#                The class is derived from Device. It represents the
#                CORBA servant object which will be accessed from the
#                network. All commands which can be executed on the
#                SlsDetector are implemented in this file.
#
# project :     TANGO Device Server
#
# copyleft :    European Synchrotron Radiation Facility
#               BP 220, Grenoble 38043
#               FRANCE
#
#=============================================================================
#         (c) - Bliss - ESRF
#=============================================================================
#
import time, string
import PyTango
from Lima import Core
from Lima import SlsDetector as SlsDetectorHw
from AttrHelper import get_attr_4u, get_attr_string_value_list

class SlsDetector(PyTango.Device_4Impl):

    Core.DEB_CLASS(Core.DebModApplication, 'LimaSlsDetector')


#------------------------------------------------------------------
#    Device constructor
#------------------------------------------------------------------
    def __init__(self,*args) :
        PyTango.Device_4Impl.__init__(self,*args)
        self.init_device()

#------------------------------------------------------------------
#    Device destructor
#------------------------------------------------------------------
    def delete_device(self):
        pass

#------------------------------------------------------------------
#    Device initialization
#------------------------------------------------------------------
    @Core.DEB_MEMBER_FUNCT
    def init_device(self):
        self.set_state(PyTango.DevState.ON)
        self.get_device_properties(self.get_device_class())

    @Core.DEB_MEMBER_FUNCT
    def getAttrStringValueList(self, attr_name):
        return get_attr_string_value_list(self, attr_name)

    def __getattr__(self,name) :
        return get_attr_4u(self, name, _SlsDetectorCam)

    def read_config_fname(self, attr) :
        attr.set_value(self.config_fname)


class SlsDetectorClass(PyTango.DeviceClass):

    class_property_list = {}

    device_property_list = {
        'config_fname':
        [PyTango.DevString,
         "Path to the SlsDetector config file",[]],
        }

    cmd_list = {
        'getAttrStringValueList':
        [[PyTango.DevString, "Attribute name"],
         [PyTango.DevVarStringArray, "Authorized String value list"]],
        }

    attr_list = {
        'config_fname':
        [[PyTango.DevString,
          PyTango.SCALAR,
          PyTango.READ]],
        }

    def __init__(self,name) :
        PyTango.DeviceClass.__init__(self,name)
        self.set_type(name)


#----------------------------------------------------------------------------
# Plugin
#----------------------------------------------------------------------------
_SlsDetectorCam = None
_SlsDetectorHwInter = None
_SlsDetectorControl = None

def get_control(config_fname, **keys) :
    global _SlsDetectorCam, _SlsDetectorHwInter, _SlsDetectorControl
    if _SlsDetectorControl is None:
	_SlsDetectorCam = SlsDetectorHw.Camera(config_fname)
        _SlsDetectorHwInter = SlsDetectorHw.Interface(_SlsDetectorCam)
        _SlsDetectorControl = Core.CtControl(_SlsDetectorHwInter)
    return _SlsDetectorControl 

def get_tango_specific_class_n_device():
    return SlsDetectorClass, SlsDetector

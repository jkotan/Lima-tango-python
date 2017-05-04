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
import numpy as np
import PyTango
from Lima import Core
from Lima import SlsDetector as SlsDetectorHw
from AttrHelper import get_attr_4u, get_attr_string_value_list

class SlsDetector(PyTango.Device_4Impl):

    Core.DEB_CLASS(Core.DebModApplication, 'LimaSlsDetector')


#------------------------------------------------------------------
#    Device constructor
#------------------------------------------------------------------

    MiliVoltSuffix = '_mv'

    def __init__(self,*args) :
        PyTango.Device_4Impl.__init__(self,*args)
        self.init_device()

        self.cam = _SlsDetectorCam
        self.model = self.cam.getModel()

        nb_modules = self.cam.getNbDetSubModules()
        name_list, idx_list, mili_volt_list = self.model.getDACInfo()
        attr_name_list = map(lambda n: 'dac_' + n, name_list)
        data_list = zip(idx_list, mili_volt_list)
        self.dac_attr_idx_list = zip(attr_name_list, data_list)
        for name, data in self.dac_attr_idx_list:
            attr_data_dict = {
                'name': name, 
                'dtype': PyTango.DevLong,
                'dformat': PyTango.SPECTRUM,
                'max_dim_x': nb_modules,
                'fget': self.read_dac,
                'fset': self.write_dac,
            }
            attr_data = PyTango.AttrData.from_dict(attr_data_dict)
            self.add_attribute(attr_data)

            idx, has_mv = data
            if has_mv:
                attr_data_dict['name'] = name + self.MiliVoltSuffix
                attr_data = PyTango.AttrData.from_dict(attr_data_dict)
                self.add_attribute(attr_data)

        name_list, idx_list, factor_list, min_val_list = self.model.getADCInfo()
        attr_name_list = map(lambda n: 'adc_' + n, name_list)
        data_list = zip(idx_list, factor_list, min_val_list)
        self.adc_attr_idx_list = zip(attr_name_list, data_list)
        for name, data in self.adc_attr_idx_list:
            attr_data_dict = {
                'name': name, 
                'dtype': PyTango.DevDouble,
                'dformat': PyTango.SPECTRUM,
                'max_dim_x': nb_modules,
                'fget': self.read_adc,
            }
            attr_data = PyTango.AttrData.from_dict(attr_data_dict)
            self.add_attribute(attr_data)

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

    def __getattr__(self,name):
        return get_attr_4u(self, name, self.cam)

    @Core.DEB_MEMBER_FUNCT
    def read_config_fname(self, attr):
        deb.Return("config_fname=%s" % self.config_fname)
        attr.set_value(self.config_fname)

    @Core.DEB_MEMBER_FUNCT
    def read_hostname_list(self, attr):
        hostname_list = self.cam.getHostnameList()
        deb.Return("config_fname=%s" % hostname_list)
        attr.set_value(hostname_list)

    @Core.DEB_MEMBER_FUNCT
    def read_raw_mode(self, attr):
        raw = self.cam.getRawMode()
        deb.Return("raw=%s" % raw)
        attr.set_value(raw)

    @Core.DEB_MEMBER_FUNCT
    def write_raw_mode(self, attr):
        raw = attr.get_write_value()
        deb.Param("raw=%s" % raw)
        self.cam.setRawMode(raw)

    @Core.DEB_MEMBER_FUNCT
    def putCmd(self, cmd):
        deb.Param("cmd=%s" % cmd)
        self.cam.putCmd(cmd);

    @Core.DEB_MEMBER_FUNCT
    def getCmd(self, cmd):
        deb.Param("cmd=%s" % cmd)
        resp = self.cam.getCmd(cmd);
        deb.Return("resp=%s" % resp)
        return resp

    @Core.DEB_MEMBER_FUNCT
    def read_dac_name_list(self, attr):
        dac_name_list = [n for n, (i, m) in self.dac_attr_idx_list]
        deb.Return("dac_name_list=%s" % (dac_name_list,))
        attr.set_value(dac_name_list)

    @Core.DEB_MEMBER_FUNCT
    def read_dac_name_list_mv(self, attr):
        mv = self.MiliVoltSuffix
        dac_name_list = [n + mv for n, (i, m) in self.dac_attr_idx_list if m]
        deb.Return("dac_name_list=%s" % (dac_name_list,))
        attr.set_value(dac_name_list)

    @Core.DEB_MEMBER_FUNCT
    def get_dac_name_mv(self, dac_name):
        mv = self.MiliVoltSuffix
        is_mv = (dac_name[-len(mv):] == mv)
        if is_mv:
            dac_name = dac_name[:-len(mv)]
        return dac_name, is_mv

    @Core.DEB_MEMBER_FUNCT
    def read_dac(self, attr):
        dac_name, mili_volt = self.get_dac_name_mv(attr.get_name())
        deb.Param("dac_name=%s, mili_volt=%s" % (dac_name, mili_volt))
        idx, has_mv = dict(self.dac_attr_idx_list)[dac_name]
        val_list = self.cam.getDACList(idx, mili_volt)
        deb.Return("val_list=%s" % val_list)
        attr.set_value(val_list)

    @Core.DEB_MEMBER_FUNCT
    def write_dac(self, attr):
        dac_name, mili_volt = self.get_dac_name_mv(attr.get_name())
        idx, has_mv = dict(self.dac_attr_idx_list)[dac_name]
        val_list = attr.get_write_value()
        deb.Param("dac_name=%s, mili_volt=%s, val_list=%s" % 
                  (dac_name, mili_volt, val_list))
        msg = None
        nb_dac = len(val_list)
        if (val_list < 0).sum() == nb_dac:
            msg = 'Invalid %s: %s' % (attr.get_name(), val_list)
        elif nb_dac == 1:
            dac_idx_list = [-1]
        elif nb_dac == self.cam.getNbDetSubModules():
            dac_idx_list = range(nb_dac)
        else:
            msg = 'Invalid %s length: %s' % (attr.get_name(), val_list)
        if msg:
            deb.Error(msg)
            raise ValueError(msg)
        for i, dac_val in zip(dac_idx_list, val_list):
            if dac_val >= 0:
                self.cam.setDAC(i, idx, dac_val, mili_volt)

    @Core.DEB_MEMBER_FUNCT
    def read_adc_name_list(self, attr):
        adc_name_list = zip(*self.adc_attr_idx_list)[0]
        deb.Return("adc_name_list=%s" % (adc_name_list,))
        attr.set_value(adc_name_list)

    @Core.DEB_MEMBER_FUNCT
    def read_adc(self, attr):
        idx, factor, min_val = dict(self.adc_attr_idx_list)[attr.get_name()]
        val_list = self.cam.getADCList(idx)
        out_arr = np.array(val_list, 'float64') * factor + min_val
        deb.Return("out_arr=%s" % out_arr)
        attr.set_value(out_arr)

    @Core.DEB_MEMBER_FUNCT
    def read_threshold_energy(self, attr):
        thres = self.cam.getThresholdEnergy()
        deb.Return("thres=%s" % thres)
        attr.set_value(thres)

    @Core.DEB_MEMBER_FUNCT
    def write_threshold_energy(self, attr):
        thres = attr.get_write_value()
        deb.Param("thres=%s" % thres)
        self.cam.setThresholdEnergy(thres)


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
        'putCmd':
        [[PyTango.DevString, "SlsDetector command"],
         [PyTango.DevVoid, ""]],
        'getCmd':
        [[PyTango.DevString, "SlsDetector command"],
         [PyTango.DevString, "SlsDetector response"]],
        }

    attr_list = {
        'config_fname':
        [[PyTango.DevString,
          PyTango.SCALAR,
          PyTango.READ]],
        'hostname_list':
        [[PyTango.DevString,
          PyTango.SPECTRUM,
          PyTango.READ, 64]],
        'dac_name_list':
        [[PyTango.DevString,
          PyTango.SPECTRUM,
          PyTango.READ, 64]],
        'dac_name_list_mv':
        [[PyTango.DevString,
          PyTango.SPECTRUM,
          PyTango.READ, 64]],
        'adc_name_list':
        [[PyTango.DevString,
          PyTango.SPECTRUM,
          PyTango.READ, 64]],
        'raw_mode':
        [[PyTango.DevBoolean,
          PyTango.SCALAR,
          PyTango.READ_WRITE]],
        'threshold_energy':
        [[PyTango.DevLong,
          PyTango.SCALAR,
          PyTango.READ_WRITE]],
        }

    def __init__(self,name) :
        PyTango.DeviceClass.__init__(self,name)
        self.set_type(name)


#----------------------------------------------------------------------------
# Plugin
#----------------------------------------------------------------------------
_SlsDetectorCam = None
_SlsDetectorHwInter = None
_SlsDetectorEiger = None
_SlsDetectorCorrection = None
_SlsDetectorControl = None

def get_control(config_fname, **keys) :
    global _SlsDetectorCam, _SlsDetectorHwInter, _SlsDetectorEiger
    global _SlsDetectorCorrection, _SlsDetectorControl
    if _SlsDetectorControl is None:
	_SlsDetectorCam = SlsDetectorHw.Camera(config_fname)
        _SlsDetectorHwInter = SlsDetectorHw.Interface(_SlsDetectorCam)
        if _SlsDetectorCam.getType() == SlsDetectorHw.Camera.EigerDet:
            _SlsDetectorEiger = SlsDetectorHw.Eiger(_SlsDetectorCam)
            _SlsDetectorCorrection = _SlsDetectorEiger.createCorrectionTask()
        else:
            raise ValueError("Unknown detector type: %s" %
                             _SlsDetectorCam.getType())
        _SlsDetectorControl = Core.CtControl(_SlsDetectorHwInter)
        if _SlsDetectorCorrection:
            _SlsDetectorControl.setReconstructionTask(_SlsDetectorCorrection)

    return _SlsDetectorControl 

def get_tango_specific_class_n_device():
    return SlsDetectorClass, SlsDetector

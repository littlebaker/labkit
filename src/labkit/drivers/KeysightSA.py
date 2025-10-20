from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal
from qcodes.instrument import Instrument
from qcodes.parameters import ManualParameter
import numpy as np
from qcodes.validators import Numbers

from devices.SA_keysightN9020B import keysightSA_N9020B


class KeysightSA(Instrument):
    def __init__(self, name: str, device_name: str,  
        metadata: Mapping[Any, Any] | None = None, label: str | None = None) -> None:
        super().__init__(name, metadata, label)

        self.sa = keysightSA_N9020B(device_name)
        
        self.add_parameter(
            "device_name",
            parameter_class=ManualParameter,
            initial_value=device_name
        )
        
        self.add_parameter(
            "fstart",
            label='Frequency start',
            set_cmd='FREQ:STAR {} GHz',
            get_cmd='FREQ:STAR?',
            get_parser=lambda x: np.round(x / 1e9),
            unit='GHz',
        )
        
        self.add_parameter(
            "fstop",
            label='Frequency stop',
            set_cmd='FREQ:STOP {} GHz',
            get_cmd='FREQ:STOP?',
            get_parser=lambda x: x / 1e9,
            unit='GHz',
        )
        
        self.add_parameter(
            "points",
            label="Points",
            set_cmd='SENS:SWE:POIN {}',
            get_cmd='SENS:SWE:POIN?',
        )
        
        self.add_parameter(
            "res_bw",
            label="Res BW",
            set_cmd="BAND {} MHZ",
            get_cmd="BAND?",
            get_parser=lambda x: x / 1e6,
            unit="MHz" 
        )
        
        self.add_parameter(
            "video_bw",
            label="Video BW",
            set_cmd="BAND:VID {} HZ",
            get_cmd="BAND:VID?",
            unit="Hz" 
        )
        
        self.add_parameter(
            "ref_level",
            label="Ref Level",
            set_cmd='DISP:WIND:TRAC:Y:RLEV {} dBm',
            get_cmd='DISP:WIND:TRAC:Y:RLEV?',
            unit="dBm" 
        )

        self.add_parameter(
            "scale_div",
            label="Scale Div",
            set_cmd='DISP:WIND:TRAC:Y:PDIV {} DB',
            get_cmd='DISP:WIND:TRAC:Y:PDIV?',
            unit="dB" 
        )

        
    def get_data(self):
        return self.sa.getdata()
        
    def write(self, cmd: str) -> None:
        return self.sa.Inst.write(cmd)
    
    def ask(self, cmd: str) -> str:
        return self.sa.Inst.query(cmd)
    
    def __getattr__(self, key: str) -> Any:
        try:
            return self.mw[key]
        except Exception: 
            pass
        return super().__getattr__(key)


def sa_param_set(sa: KeysightSA, fstart: float, fstop: float, points:float,res_bw:float,video_bw:float):
    sa.fstart(fstart)
    sa.fstop(fstop)
    sa.points(points)
    sa.res_bw(res_bw)
    sa.video_bw(video_bw)
   


from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal
from qcodes.instrument import Instrument
from qcodes.parameters import ManualParameter

from qcodes.validators import Numbers

from devices.SMB_100A import MW


class KeysightMWG(Instrument):
    def __init__(self, name: str, device_name: str,  
        metadata: Mapping[Any, Any] | None = None, label: str | None = None) -> None:
        super().__init__(name, metadata, label)

        self.mw = MW(device_name)
        
        self.device_name = self.add_parameter(
            "device_name",
            parameter_class=ManualParameter,
            initial_value=device_name
        )
        
        self.power = self.add_parameter(
            "power",
            label='Amplitude',
            set_cmd=lambda x: self.mw.MW_setpower(x),
            get_cmd=':POW?',
            get_parser=float,
            unit='dBm',
        )
        
        self.phase = self.add_parameter(
            "phase",
            label="Phase",
            set_cmd='PHAS {}DEG',
            get_cmd=':PHAS?',
            get_parser=float,
            unit="deg"
        )
        
        # Setting frequency range
        self.freq = self.add_parameter(
            'freq',
            label='Frequency',
            get_cmd='FREQ:CW?',
            get_parser=lambda x: float(x)*1e-9,
            set_cmd='FREQ:CW {}GHz',
            unit='GHz',
            vals=Numbers(min_value=250e-6,max_value=40)
        )

    
    
    def rf_output(self, sw: Literal["on", "off"]="on"):
        assert sw in ["on", "off"]
        if sw == "on":
            self.mw.Inst.write('OUTP ON')
        else:
            self.mw.Inst.write('OUTP OFF')
        
        
        
    def write(self, cmd: str) -> None:
        return self.mw.Inst.write(cmd)
    
    def ask(self, cmd: str) -> str:
        return self.mw.Inst.query(cmd)
    
    def __getattr__(self, key: str) -> Any:
        try:
            return self.mw[key]
        except Exception: 
            pass
        return super().__getattr__(key)


def mw_param_set(mw: KeysightMWG, amp: float, phase: float, freq:float):
    mw.power(amp)
    mw.phase(phase)
    mw.freq(freq)
   


if __name__ == "__main__":
    mw3 = KeysightMWG("MW3", "mw3")
    
    mw_param_set(mw3, -11, 30, 4.555)
    
    mw3.rf_output()
    
    
    
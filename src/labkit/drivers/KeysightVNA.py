from __future__ import annotations


import numpy as np

from collections.abc import Mapping, Sequence
from typing import Any
from qcodes.instrument import Instrument
from qcodes.parameters import ManualParameter
from deprecated import deprecated
from qcodes.validators import Numbers, Enum,Ints, Bool
from pyvisa import constants
import pyvisa


trace_lookup = {
    "S11": 11,
    "S12": 12,
    "S13": 13,
    "S14": 14,
    "S21": 21,
    "S22": 22,
    "S23": 23,
    "S24": 24,
    "S31": 31,
    "S32": 32,
    "S33": 33,
    "S34": 34,
    "S41": 41,
    "S42": 42,
    "S43": 43,
    "S44": 44,
    "S2141": 2141,
    "S2143": 2143,
    "all": 4,
}

class KeysightVNA(Instrument):
    def __init__(
        self,
        name: str,
        device_name: str,
        metadata: Mapping[Any, Any] | None = None,
        label: str | None = None,
    ) -> None:
        super().__init__(name, metadata, label)

        self.vna = keysight_vna(device_name, timeout=5000)

        self.device_name = self.add_parameter(
            "device_name", parameter_class=ManualParameter, initial_value=device_name
        )
        self.trace = self.add_parameter(
            "trace", 
            label="Trace",
            set_cmd=lambda x: self.vna.set_trace(trace_lookup.get(x)),
            vals=Enum("S11","S21", "S43", "S23", "S41","S2141", "all", "S2143")
        )

        self.power = self.add_parameter(
            "power",
            label="Power",
            set_cmd=lambda x: self.vna.set_power(x),
            unit="dBm",
        )

        self.ifband = self.add_parameter(
            "ifband",
            label="IF Bandwidth",
            get_cmd="SENS:BAND?",
            get_parser=float,
            set_cmd="SENS:BAND:RES {:.2f}",
            unit="Hz",
            vals=Numbers(min_value=1, max_value=15e6),
        )

        # Number of points in a sweep
        self.points = self.add_parameter(
            "points",
            label="Points",
            get_cmd="SENS:SWE:POIN?",
            get_parser=int,
            set_cmd="SENS:SWE:POIN {}",
            unit="",
            vals=Numbers(min_value=1, max_value=100001),
        )

        # Electrical delay
        self.electrical_delay = self.add_parameter(
            "electrical_delay",
            label="Electrical Delay",
            get_cmd="CALC:CORR:EDEL:TIME?",
            get_parser=float,
            set_cmd="CALC:CORR:EDEL:TIME {:.6e}ns",
            unit="ns",
            vals=Numbers(min_value=0, max_value=100000),
        )

        self.power_mode_source1 = self.add_parameter(
            "power_mode_source1",
            label="Power Mode (Source 1)",
            get_cmd="SOURce:POWer1:MODE?",
            set_cmd="SOURce:POWer1:MODE {}",
            vals=Enum("ON", "OFF")
        )
    
        # Setting frequency range
        self.fstart = self.add_parameter(
            "fstart",
            label="Start Frequency",
            get_cmd="SENS:FREQ:STAR?",
            get_parser=lambda x: float(x) / 1e9,
            set_cmd="SENS:FREQ:STAR {}GHz",
            unit="GHz",
            vals=Numbers(min_value=300e-6, max_value=13.5),
        )
        self.fstop = self.add_parameter(
            "fstop",
            label="Stop Frequency",
            get_cmd="SENS:FREQ:STOP?",
            get_parser=lambda x: float(x) / 1e9,
            set_cmd="SENS:FREQ:STOP {}GHz",
            unit="GHz",
            vals=Numbers(min_value=300e-6, max_value=13.5),
        )

        self.average = self.add_parameter(
            "average",
            label="Averaging Count",
            get_cmd="SENS:AVER:COUN?",
            get_parser=int,  # 因为平均次数通常是整数
            set_cmd="SENSe:AVERage:COUNt {}",
            unit="counts",  # 单位通常是次数
            vals=Ints(min_value=1, max_value=999),  # 根据你的设备允许的最大和最小平均次数调整
        )

        self.trigger_continuous = self.add_parameter(
            "trigger_continuous",
            vals=Bool(),
            get_cmd="INIT:CONT?",
            set_cmd=lambda v: self.write(f"INIT:CONT {'ON' if v else 'OFF'}"),
            get_parser=lambda s: bool(int(float(s))),
        )


        self.fcenter = self.add_parameter(
            "fcenter",
            label="Center Frequency",
            get_cmd="SENS:FREQ:CENT?",
            get_parser=lambda x: float(x) / 1e9,
            set_cmd="SENS:FREQ:CENT {}GHz",
            unit="GHz",
            vals=Numbers(min_value=300e-6, max_value=13.5),
        )
        self.data = self.add_parameter(
            "data",
            label="Data",
            get_cmd=lambda: self.vna.get_data(),
        )

        self.data_S21 = self.add_parameter(
            "data_S21",
            label="S21 Data",
            get_cmd=lambda: self.vna.get_data_S21(),
        )

        self.data_S43 = self.add_parameter(
            "data_S43",
            label="S43 Data",
            get_cmd=lambda: self.vna.get_data_S43(),
        )

        self.data_S41 = self.add_parameter(
            "data_S41",
            label="S41 Data",
            get_cmd=lambda: self.vna.get_data_S41(),
        )

        self.data_S23 = self.add_parameter(
            "data_S23",
            label="S23 Data",
            get_cmd=lambda: self.vna.get_data_S23(),
        )

        self.data_all = self.add_parameter(
            "data_all",
            label="All Data",
            get_cmd=lambda: self.vna.get_data_all(),
        )

        
        self.trigger_mode = self.add_parameter(
            "trigger_mode",
            label="Trigger mode",
            get_cmd="SENS:SWE:MODE?",
            set_cmd="SENS:SWE:MODE {}",
            vals=Enum("HOLD", "CONT", "GRO", "SING")
        )

    def reload(self):
        self.vna = keysight_vna(self.name, timeout=300)

    def write(self, cmd: str) -> None:
        return self.vna.Inst.write(cmd)

    def ask(self, cmd: str) -> str:
        return self.vna.Inst.query(cmd)

    def __getattr__(self, key: str) -> Any:
        try:
            return self.vna[key]
        except Exception:
            pass
        return super().__getattr__(key)

    @deprecated
    def _get_extract_data(self):
        x = self.vna.get_data()
        return np.real(x), np.imag(x)

    def snapshot_base(
        self,
        update: bool | None = False,
        params_to_skip_update: Sequence[str] | None = None,
    ) -> dict[Any, Any]:

        if params_to_skip_update is None:
            ptsu = []
        else:
            ptsu = (
                list(params_to_skip_update)
            )
        if "data" not in ptsu:
            ptsu.append("data")
        return super().snapshot_base(update, ptsu)


def vna_param_set(
    vna: KeysightVNA, trace: str, vnapwr:float, fstart: float, fstop: float, ifband: int, points: int, edelay=0,average=1,
):
    vna.trace(trace)
    vna.power(vnapwr)
    vna.fstart(fstart)
    vna.fstop(fstop)
    vna.ifband(ifband)
    vna.points(points)
    vna.electrical_delay(edelay)
    vna.average(average)




class keysight_vna(object):
    def __init__(self, name, timeout=300):
        Rm = pyvisa.ResourceManager()
        vnanum = {
            # "vna1": "TCPIP::172.25.146.85::inst0::INSTR",
            # "vna2": "TCPIP::172.25.146.89::inst0::INSTR",
            "vna1": "TCPIP::172.25.146.85::5025::SOCKET",
            "vna4port": "TCPIP::172.25.146.89::5025::SOCKET",
            "vna41": "TCPIP::172.25.146.41::5025::SOCKET",
            "vna2port": "TCPIP::172.25.146.89::5025::SOCKET",

        }
        self.trace = None

        self.Inst = Rm.open_resource(
            vnanum[name],
            open_timeout=timeout,
            access_mode=constants.AccessModes.shared_lock,
        )
        # For Serial and TCP/IP socket connections enable the read Termination Character, or read's will timeout
        if self.Inst.resource_name.startswith('ASRL') or self.Inst.resource_name.endswith('SOCKET'):
            self.Inst.read_termination = '\n'
            
        # I don't know why this is important
        self.Inst.timeout = timeout * 1000
        self.Inst.write(
            "*RST",
        )
        print(name + " Connect OK")
        
    def set_trace(self, trace: int) -> None:
        # 小工具：统一定义与绑定
        def _meas_name(sp: str) -> str:
            return f"MySMea{sp}"

        def _define(sp: str) -> str:
            name = _meas_name(sp)
            # 用引号包裹测量名，避免空格与特殊字符问题
            self.Inst.write(f"CALCulate1:PARameter:DEFine {name},{sp}")
            return name

        def _feed(trace_idx: int, name: str) -> None:
            self.Inst.write("DISPlay:WINDow1:STATE ON")
            self.Inst.write(f"DISPlay:WINDow1:TRACe{trace_idx}:FEED {name}")

        # 预置与等待
        self.Inst.write("SYSTem:PREset")
        self.Inst.write("SYSTem:FPReset")
        self.Inst.write("INIT:CONT OFF")
        self.Inst.query("*OPC?")

        # 各种 trace 编码到 (窗口trace序号, S参数) 的映射
        plan_map = {
            4:    [(1, "S21"), (2, "S43"), (3, "S41"), (4, "S23")],
            41:   [(3, "S41")],
            42:   [(3, "S42")],
            43:   [(3, "S43")],
            44:   [(3, "S44")],
            21:   [(1, "S21")],
            22:   [(4, "S22")],
            23:   [(4, "S23")],
            24:   [(4, "S24")],
            11:   [(1, "S11")],
            12:   [(1, "S12")],
            13:   [(1, "S13")],
            14:   [(1, "S14")],
            242:  [(1, "S21"), (2, "S11"), (3, "S12"), (4, "S22")],
            2141: [(1, "S21"), (3, "S41")],
            2143: [(1, "S21"), (3, "S43")],
        }
        plan = plan_map.get(trace, [(1, "S21")])  # 默认 S21 到 Trace1

        # 定义测量并绑定到显示窗口的指定 trace
        for trace_idx, sp in plan:
            name = _define(sp)
            _feed(trace_idx, name)

        # 标题与注释（与原版一致）
        self.Inst.write("DISPlay:WINDow1:TITLe:STATe ON")
        self.Inst.write("DISPlay:ANNotation:FREQuency ON")

        # 保存 trace，并设置触发域与连续扫频
        self.trace = trace
        self.Inst.write("TRIG:SCOPe ALL")
        self.Inst.write("SENSe:SWEep:MODE CONTinuous")

    def average_sweep(self, N: int = 16, mode: str = "NORM") -> np.ndarray:
        """
        执行一次 N 次平均的扫频并返回复数 SDATA。
        - 强制 INIT:CONT OFF，确保确定性。
        - mode='NORM' 时执行 N 次后停止；'MOV' 则为滚动平均窗口（一般不建议用于确定性采集）。
        """

        prev_cont = bool(int(float(self.ask("INIT:CONT?"))))
        if prev_cont:
            self.trigger_continuous(False)

        self._prepare_avg(N=N, mode=mode)
        self._trigger_single()           # 等待 *OPC? 返回，代表 N 次完成
        data = self._read_sdata_complex()

        # 恢复之前的连续模式
        if prev_cont:
            self.trigger_continuous(True)

        return data

    def rst(self):
        self.Inst.write("*RST")
        pass  # zzz只要s21

    def get_allSet(self):
        strafre = self.Inst.query("SENSe:FREQuency:STARt?")
        Stopfre = self.Inst.query("SENSe:FREQuency:STOP?")
        points = self.Inst.query("SENSe:SWEep:POINts?")
        avg = self.Inst.query("SENSe:AVERage:COUNt?")
        Ifband = self.Inst.query("SENS:BAND:RES?")
        power = self.Inst.query("SOURce:POWer?")
        #        nomal_set={strafre,Stopfre,points,avg,Ifband,power}
        return strafre, Stopfre, points, avg, Ifband, power

    def _setAverage(self, N):
        N = int(N)
        if N > 1:
            self.instrhandle.write("SENS:AVER ON")
            self.instrhandle.write("SENS:AVER:CLE")
            self.instrhandle.write("SENS:AVER:MODE AUTO")
            self.instrhandle.write("SENSe:AVERage:COUNt {}".format(N))
            
    def reset(self):
        self.Inst.write(
            "*RST",
        )
        self.Inst.write("SYSTem:PREset")
        self.Inst.write("SYSTem:FPReset")
        self.Inst.write("INIT:CONT OFF")
        self.Inst.query("*OPC?")

    def set_startstopFre(self, strafre, stopfre):
        self.Inst.write("SENSe:FREQuency:STARt {}".format(float(strafre) * 1e9))
        self.Inst.write("SENSe:FREQuency:STOP {}".format(float(stopfre) * 1e9))  # Ghz

    #        self.Inst.write('INITiate:IMMediate;*wai')
    #        self.Inst.write('Display:WINDow1:TRACe1:Y:Scale:AUTO')
    def set_power(self, power):
        self.Inst.write("SOURce:POWer {}".format(float(power)))

    def set_points_band(self, points, ifband):
        self.Inst.write("SENSe:SWE:POIN {}".format(int(points)))
        self.Inst.write("SENSe:BAND:RES {}".format(float(ifband)))

    def set_allSetting(self, strafre, stopfre, points, avg, ifband, power):
        self.Inst.write("SENSe:FREQuency:STARt {}".format(float(strafre) * 1e9))
        self.Inst.write("SENSe:FREQuency:STOP {}".format(float(stopfre) * 1e9))  # Ghz
        self.Inst.write("SENSe:SWE:POIN {}".format(int(points)))
        self.Inst.write("SENSe:AVERage:COUNt {}".format(int(avg)))
        self.Inst.write("SENSe:BAND:RES {}".format(float(ifband)))
        #        self.Inst.write('SOURce:POWer{}'.format(power))
        self.Inst.write("SOURce:POWer {}".format(float(power)))
        print("write data")
        print(strafre, stopfre, points, avg, ifband, power)

    def testwrite_comand(self, string):
        return self.Inst.write(string)

    def testquery_comand(self, string):
        return self.Inst.query(string)

    def get_data(self):
        print( self.trace)
        if self.trace in [ 11,12,13,14,21,22,23,24,31,32,33,34,41,42,43,44,]:
            self.Inst.write("FORMat:DATA REAL,64")
            self.Inst.write("FORMat:DATA ASCII")
            self.Inst.query("*OPC?") 
            self.Inst.write("INITiate:IMMediate;*wai")
            self.Inst.query("*OPC?") 

            # 选择特定的trace
            self.Inst.write("CALCulate:PARameter:SELect " f"MySMeaS{self.trace}" "")
            self.Inst.query("*OPC?")  # 等待操作完成
            sawdata = self.Inst.query("CALCulate:DATA? SDATA")
            sawdata1 = sawdata.split(",")
            Sdata = []
            for i in range(len(sawdata1)):
                if i % 2 == 0:
                    Sdata.append(complex(float(sawdata1[i]), float(sawdata1[i + 1])))
            Sdata = np.array(Sdata)
            return Sdata
        elif self.trace == 2143:
            return self.get_data_S2143()
        elif self.trace == 4:
            return self.get_data_all()

        raise Exception("Unknown trace: ", self.trace)


    def fixdata(self, sawdata):
        sawdata1 = sawdata.split(",")
        Sdata = []
        for i in range(len(sawdata1)):
            if i % 2 == 0:
                Sdata.append(complex(float(sawdata1[i]), float(sawdata1[i + 1])))
        Sdata = np.array(Sdata)
        return Sdata

    def get_data_all(self):
        self.Inst.write("FORMat:DATA REAL,64")
        self.Inst.write("FORMat:DATA ASCII")
        self.Inst.write("INITiate:IMMediate;*wai")
        self.Inst.write("CALCulate:PARameter:SELect " "MySMeaS21" "")
        sawdata21 = self.Inst.query("CALCulate:DATA? SDATA")
        self.Inst.write("CALCulate:PARameter:SELect " "MySMeaS43" "")
        sawdata43 = self.Inst.query("CALCulate:DATA? SDATA")
        self.Inst.write("CALCulate:PARameter:SELect " "MySMeaS41" "")
        sawdata41 = self.Inst.query("CALCulate:DATA? SDATA")
        self.Inst.write("CALCulate:PARameter:SELect " "MySMeaS23" "")
        sawdata23 = self.Inst.query("CALCulate:DATA? SDATA")
        self.Inst.query("*OPC?")  # 等待操作完成
        Sdata21 = self.fixdata(sawdata21)
        Sdata43 = self.fixdata(sawdata43)
        Sdata41 = self.fixdata(sawdata41)
        Sdata23 = self.fixdata(sawdata23)
        return Sdata21, Sdata43, Sdata41, Sdata23
    

    def get_data_S2143(self):
        self.Inst.write("FORMat:DATA REAL,64")
        self.Inst.write("FORMat:DATA ASCII")
        self.Inst.write("INITiate:IMMediate;*wai")
        self.Inst.write("CALCulate:PARameter:SELect " "MySMeaS21" "")
        sawdata21 = self.Inst.query("CALCulate:DATA? SDATA")
        self.Inst.write("CALCulate:PARameter:SELect " "MySMeaS43" "")
        sawdata43 = self.Inst.query("CALCulate:DATA? SDATA")
        self.Inst.query("*OPC?")  # 等待操作完成
        Sdata21 = self.fixdata(sawdata21)
        Sdata43 = self.fixdata(sawdata43)

        return Sdata21, Sdata43

    def get_data_all_2port(self):
        self.Inst.write("FORMat:DATA REAL,64")
        self.Inst.write("FORMat:DATA ASCII")
        self.Inst.write("INITiate:IMMediate;*wai")
        self.Inst.write("CALCulate:PARameter:SELect " "MySMeaS21" "")
        sawdata21 = self.Inst.query("CALCulate:DATA? SDATA")
        self.Inst.write("CALCulate:PARameter:SELect " "MySMeaS11" "")
        sawdata11 = self.Inst.query("CALCulate:DATA? SDATA")
        self.Inst.write("CALCulate:PARameter:SELect " "MySMeaS12" "")
        sawdata12 = self.Inst.query("CALCulate:DATA? SDATA")
        self.Inst.write("CALCulate:PARameter:SELect " "MySMeaS22" "")
        sawdata22 = self.Inst.query("CALCulate:DATA? SDATA")
        Sdata21 = self.fixdata(sawdata21)
        Sdata11 = self.fixdata(sawdata11)
        Sdata12 = self.fixdata(sawdata12)
        Sdata22 = self.fixdata(sawdata22)
        return Sdata21, Sdata11, Sdata12, Sdata22

    def Scan_freSpectrum(self, powers):
        S_data = list()
        for i in range(len(powers)):
            self.set_power(powers[i])
            f, data = self.get_data()
            S_data.append(data)
            if i % (int(len(powers) / 10)) == 0:
                print("scan_Fr: {:.0f}% completed.".format((i + 1) / len(powers) * 100))
        return f, np.array(S_data)

    def close(self):
        self.Inst.close()
        pass

    def two_tone_vna(self, channel=1):
        self.Inst.write(
            "TRIGger:SEQuence:SOURce MANual"
        )  #'TRIGger:SEQuence:SOURce ''External'''
        self.Inst.write(
            "TRIG:SCOP CURRENT"
        )  # TRIG:SCOP CURRENT   #TRIGger:SEQuence:SCOPe ''Chan''
        if channel == 1:
            self.Inst.write("SENSe:SWEep:TRIGger:DELay {}".format(float(1) * 1e-3))
            self.Inst.write("TRIG:CHAN:AUX2 0")
            self.Inst.write("TRIG:CHAN:AUX1 1")
            self.Inst.write("TRIG:CHAN:AUX1:OPOL POS")
            self.Inst.write("TRIG:CHAN:AUX1:POS AFT")
            self.Inst.write("TRIG:CHAN:AUX1:INTerval POINt")
            self.Inst.write("TRIG:CHAN:AUX1:DUR 10E-6")
            pass
        elif channel == 2:
            self.Inst.write("SENSe:SWEep:TRIGger:DELay {}".format(float(1) * 1e-3))
            self.Inst.write("TRIG:CHAN:AUX1 0")
            self.Inst.write("TRIG:CHAN:AUX2 1")
            self.Inst.write("TRIG:CHAN:AUX2:OPOL POS")
            self.Inst.write("TRIG:CHAN:AUX2:POS AFT")
            self.Inst.write("TRIG:CHAN:AUX2:INTerval POINt")
            self.Inst.write("TRIG:CHAN:AUX2:DUR 10E-6")
            pass
        else:
            raise Exception("Channel must 1 and 2.")


    def poweroff(self, i):
        self.Inst.write("SOURce:POWer{}:MODE OFF".format(int(i)))

    def SingleSweep(self):
        self.Inst.write("SENSe:SWEep:MODE Single")





if __name__ == "__main__":
    vna = KeysightVNA("VNA1", "vna1", "S21")
    print(vna.address(), vna.trace())

    vna_param_set(vna, 6e9, 7e9, 30, 101)

    from pprint import pprint  # noqa: F401
    # pprint(vna.snapshot())

    print(vna.data_all())
    # import sys, traceback, threading
    # thread_names = {t.ident: t.name for t in threading.enumerate()}
    # print(thread_names)
    # for thread_id, frame in sys._current_frames().items():
    #     print("Thread %s:" % thread_names.get(thread_id, thread_id))
    #     traceback.print_stack(frame)
    #     print()
    # sys.exit(1)

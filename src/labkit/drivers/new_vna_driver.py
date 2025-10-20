from __future__ import annotations

import numpy as np
from collections.abc import Mapping, Sequence
from typing import Any
from qcodes.instrument import Instrument
from qcodes.parameters import ManualParameter
from qcodes.validators import Numbers, Enum, Ints, Bool
from pyvisa import constants
import pyvisa
from typing import Literal

trace_lookup = {
    "S11": 11, "S12": 12, "S13": 13, "S14": 14,
    "S21": 21, "S22": 22, "S23": 23, "S24": 24,
    "S31": 31, "S32": 32, "S33": 33, "S34": 34,
    "S41": 41, "S42": 42, "S43": 43, "S44": 44,
    "S2141": 2141, "S2143": 2143,
    "all": 4,
}

class KeysightVNA(Instrument):
    """
    合并后的单一类：
    - 作为 QCoDeS Instrument 提供参数接口
    - 内部直接用 pyvisa (self.Inst) 与设备通信
    - 方法与原来两类保持一致或等价
    """

    def __init__(
        self,
        name: str,
        device_name: str,
        metadata: Mapping[Any, Any] | None = None,
        label: str | None = None,
    ) -> None:
        super().__init__(name, metadata=metadata, label=label)

        # ---- 原 keysight_vna.__init__ 合并 ----
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
            vnanum[device_name],
            open_timeout=5000,  # 与你上层传入保持一致
            access_mode=constants.AccessModes.shared_lock,
        )
        if self.Inst.resource_name.startswith("ASRL") or self.Inst.resource_name.endswith("SOCKET"):
            self.Inst.read_termination = "\n"
        self.Inst.timeout = 5000 * 1000
        self.Inst.write("*RST")
        print(device_name + " Connect OK")

        # ---- QCoDeS 参数（保留原 KeysightVNA 参数定义）----
        self.device_name = self.add_parameter(
            "device_name", parameter_class=ManualParameter, initial_value=device_name
        )
        self.trace_param = self.add_parameter(  # 避免与 self.trace 冲突，命名 trace_param
            "trace",
            label="Trace",
            set_cmd=lambda x: self.set_trace(trace_lookup.get(x)),
            vals=Enum("S11", "S21", "S43", "S23", "S41", "S2141", "all", "S2143"),
        )
        self.power = self.add_parameter(
            "power",
            label="Power",
            set_cmd=lambda x: self.set_power(x),
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
        self.points = self.add_parameter(
            "points",
            label="Points",
            get_cmd="SENS:SWE:POIN?",
            get_parser=int,
            set_cmd="SENS:SWE:POIN {}",
            unit="",
            vals=Numbers(min_value=1, max_value=100001),
        )
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
            vals=Enum("ON", "OFF"),
        )
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
            get_parser=int,
            set_cmd="SENSe:AVERage:COUNt {}",
            unit="counts",
            vals=Ints(min_value=1, max_value=999),
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
            get_cmd=lambda: self.get_data(),
        )
        self.data_S21 = self.add_parameter(
            "data_S21",
            label="S21 Data",
            get_cmd=lambda: self.get_data_S21(),
        )
        self.data_S43 = self.add_parameter(
            "data_S43",
            label="S43 Data",
            get_cmd=lambda: self.get_data_S43(),
        )
        self.data_S41 = self.add_parameter(
            "data_S41",
            label="S41 Data",
            get_cmd=lambda: self.get_data_S41(),
        )
        self.data_S23 = self.add_parameter(
            "data_S23",
            label="S23 Data",
            get_cmd=lambda: self.get_data_S23(),
        )
        self.data_all = self.add_parameter(
            "data_all",
            label="All Data",
            get_cmd=lambda: self.get_data_all(),
        )
        self.trigger_mode = self.add_parameter(
            "trigger_mode",
            label="Trigger mode",
            get_cmd="SENS:SWE:MODE?",
            set_cmd="SENS:SWE:MODE {}",
            vals=Enum("HOLD", "CONT", "GRO", "SING"),
        )

    # ---- 通用 I/O 封装，供参数与方法调用 ----
    def write(self, cmd: str) -> None:
        self.Inst.write(cmd)

    def ask(self, cmd: str) -> str:
        return self.Inst.query(cmd)


    def snapshot_base(
        self,
        update: bool | None = False,
        params_to_skip_update: Sequence[str] | None = None,
    ) -> dict[Any, Any]:
        ptsu = list(params_to_skip_update) if params_to_skip_update else []
        if "data" not in ptsu:
            ptsu.append("data")
        return super().snapshot_base(update, ptsu)

    # ---- 合并原 keysight_vna 的方法 ----
    def set_trace(self, trace: int) -> None:
        # 小工具：统一定义与绑定（保持你最新版本的无引号风格）
        def _meas_name(sp: str) -> str:
            return f"MySMea{sp}"

        def _define(sp: str) -> str:
            name = _meas_name(sp)
            self.Inst.write(f"CALCulate1:PARameter:DEFine {name},{sp}")
            return name

        def _feed(trace_idx: int, name: str) -> None:
            self.Inst.write("DISPlay:WINDow1:STATE ON")
            self.Inst.write(f"DISPlay:WINDow1:TRACe{trace_idx}:FEED {name}")

        self.Inst.write("SYSTem:PREset")
        self.Inst.write("SYSTem:FPReset")
        self.Inst.write("INIT:CONT OFF")
        self.Inst.query("*OPC?")

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
        plan = plan_map.get(trace, [(1, "S21")])

        for trace_idx, sp in plan:
            name = _define(sp)
            _feed(trace_idx, name)

        self.Inst.write("DISPlay:WINDow1:TITLe:STATe ON")
        self.Inst.write("DISPlay:ANNotation:FREQuency ON")

        self.trace = trace
        self.Inst.write("TRIG:SCOPe ALL")
        self.Inst.write("SENSe:SWEep:MODE CONTinuous")

    def average_sweep(self, N: int = 16, mode: Literal["POINt", "SWEEP"] = "POINt"):
        """
        执行一次 N 次平均的扫频并返回复数 SDATA。
        - 若当前 trace 是单测量（如 11/21/41/...），返回 ndarray
        - 若是组合测量（如 4/2143/242），按既定顺序返回 tuple(ndarray, ...)
        """
        # 根据 set_trace 的定义，复用同一映射
        plan_map = {
            4:    ("S21", "S43", "S41", "S23"),
            41:   ("S41",),
            42:   ("S42",),
            43:   ("S43",),
            44:   ("S44",),
            21:   ("S21",),
            22:   ("S22",),
            23:   ("S23",),
            24:   ("S24",),
            11:   ("S11",),
            12:   ("S12",),
            13:   ("S13",),
            14:   ("S14",),
            242:  ("S21", "S11", "S12", "S22"),
            2141: ("S21", "S41"),
            2143: ("S21", "S43"),
        }

        #设置模式
        self.write(f"SENS:AVER:MODE {mode}")

        if self.trace is None:
            raise RuntimeError("No trace configured. Please call set_trace() first.")

        s_list = plan_map.get(self.trace, ("S21",))  # 默认按 S21
        # 记录并暂时关闭连续模式，保证确定性
        prev_cont = bool(int(float(self.ask("INIT:CONT?"))))
        if prev_cont:
            self.trigger_continuous(False)

        # 建议与 get_data 保持一致的格式设定
        self.Inst.write("FORMat:DATA REAL,64")
        self.Inst.write("FORMat:DATA ASCII")
        _ = self.ask("*OPC?")

        # 配置平均
        self.write("SENS:AVER ON")
        self.write(f"SENSe:AVERage:COUNt {int(N)}")
        # self.write(f"SENS:AVER:TCON {'MOV' if mode.upper() == 'MOV' else 'NORM'}")
        self.write("SENS:AVER:CLE")
        _ = self.ask("*OPC?")

        # 触发一次测量（仪器会做 N 次平均）
        self.write("INITiate:IMMediate;*WAI")
        _ = self.ask("*OPC?")

        # 关闭平均模式
        self.write("SENS:AVER OFF")

        # 逐个 S 参数读取
        results = []
        for sp in s_list:
            self.Inst.write(f"CALCulate:PARameter:SELect MySMea{sp}")
            _ = self.ask("*OPC?")
            s = self.Inst.query("CALCulate:DATA? SDATA")
            results.append(self.fixdata(s))

        # 恢复连续模式
        if prev_cont:
            self.trigger_continuous(True)

        # 单测量返回 ndarray；组合返回 tuple
        return results[0] if len(results) == 1 else tuple(results)


    def rst(self):
        self.Inst.write("*RST")
        # 保持原注释：zzz只要s21

    def get_allSet(self):
        strafre = self.Inst.query("SENSe:FREQuency:STARt?")
        Stopfre = self.Inst.query("SENSe:FREQuency:STOP?")
        points = self.Inst.query("SENSe:SWEep:POINts?")
        avg = self.Inst.query("SENSe:AVERage:COUNt?")
        Ifband = self.Inst.query("SENS:BAND:RES?")
        power = self.Inst.query("SOURce:POWer?")
        return strafre, Stopfre, points, avg, Ifband, power

    def _setAverage(self, N):
        N = int(N)
        if N > 1:
            # 修正句柄以可用（不改变“开启平均并设置次数”的含义）
            self.Inst.write("SENS:AVER ON")
            self.Inst.write("SENS:AVER:CLE")
            self.Inst.write("SENS:AVER:MODE AUTO")
            self.Inst.write(f"SENSe:AVERage:COUNt {N}")

    def reset(self):
        self.Inst.write("*RST")
        self.Inst.write("SYSTem:PREset")
        self.Inst.write("SYSTem:FPReset")
        self.Inst.write("INIT:CONT OFF")
        self.Inst.query("*OPC?")

    def set_startstopFre(self, strafre, stopfre):
        self.Inst.write(f"SENSe:FREQuency:STARt {float(strafre) * 1e9}")
        self.Inst.write(f"SENSe:FREQuency:STOP {float(stopfre) * 1e9}")

    def set_power(self, power):
        self.Inst.write(f"SOURce:POWer {float(power)}")

    def set_points_band(self, points, ifband):
        self.Inst.write(f"SENSe:SWE:POIN {int(points)}")
        self.Inst.write(f"SENSe:BAND:RES {float(ifband)}")

    def set_allSetting(self, strafre, stopfre, points, avg, ifband, power):
        self.Inst.write(f"SENSe:FREQuency:STARt {float(strafre) * 1e9}")
        self.Inst.write(f"SENSe:FREQuency:STOP {float(stopfre) * 1e9}")
        self.Inst.write(f"SENSe:SWE:POIN {int(points)}")
        self.Inst.write(f"SENSe:AVERage:COUNt {int(avg)}")
        self.Inst.write(f"SENSe:BAND:RES {float(ifband)}")
        self.Inst.write(f"SOURce:POWer {float(power)}")
        print("write data")
        print(strafre, stopfre, points, avg, ifband, power)

    def testwrite_comand(self, string):
        return self.Inst.write(string)

    def testquery_comand(self, string):
        return self.Inst.query(string)

    def get_data(self):
        print(self.trace)
        if self.trace in [11,12,13,14,21,22,23,24,31,32,33,34,41,42,43,44]:
            self.Inst.write("FORMat:DATA REAL,64")
            self.Inst.write("FORMat:DATA ASCII")
            self.Inst.query("*OPC?")
            self.Inst.write("INITiate:IMMediate;*wai")
            self.Inst.query("*OPC?")
            # 选择特定的trace（修正为明确的 SCPI）
            self.Inst.write(f"CALCulate:PARameter:SELect MySMeaS{self.trace}")
            self.Inst.query("*OPC?")
            sawdata = self.Inst.query("CALCulate:DATA? SDATA")
            return self.fixdata(sawdata)
        elif self.trace == 2143:
            return self.get_data_S2143()
        elif self.trace == 4:
            return self.get_data_all()
        raise Exception("Unknown trace: ", self.trace)

    def fixdata(self, sawdata):
        sawdata1 = sawdata.split(",")
        Sdata = []
        for i in range(0, len(sawdata1)-1, 2):
            Sdata.append(complex(float(sawdata1[i]), float(sawdata1[i + 1])))
        return np.array(Sdata)

    def get_data_all(self):
        self.Inst.write("FORMat:DATA REAL,64")
        self.Inst.write("FORMat:DATA ASCII")
        self.Inst.write("INITiate:IMMediate;*wai")
        self.Inst.write("CALCulate:PARameter:SELect MySMeaS21")
        sawdata21 = self.Inst.query("CALCulate:DATA? SDATA")
        self.Inst.write("CALCulate:PARameter:SELect MySMeaS43")
        sawdata43 = self.Inst.query("CALCulate:DATA? SDATA")
        self.Inst.write("CALCulate:PARameter:SELect MySMeaS41")
        sawdata41 = self.Inst.query("CALCulate:DATA? SDATA")
        self.Inst.write("CALCulate:PARameter:SELect MySMeaS23")
        sawdata23 = self.Inst.query("CALCulate:DATA? SDATA")
        self.Inst.query("*OPC?")
        return (self.fixdata(sawdata21),
                self.fixdata(sawdata43),
                self.fixdata(sawdata41),
                self.fixdata(sawdata23))

    def get_data_S2143(self):
        self.Inst.write("FORMat:DATA REAL,64")
        self.Inst.write("FORMat:DATA ASCII")
        self.Inst.write("INITiate:IMMediate;*wai")
        self.Inst.write("CALCulate:PARameter:SELect MySMeaS21")
        sawdata21 = self.Inst.query("CALCulate:DATA? SDATA")
        self.Inst.write("CALCulate:PARameter:SELect MySMeaS43")
        sawdata43 = self.Inst.query("CALCulate:DATA? SDATA")
        self.Inst.query("*OPC?")
        return self.fixdata(sawdata21), self.fixdata(sawdata43)

    def get_data_all_2port(self):
        self.Inst.write("FORMat:DATA REAL,64")
        self.Inst.write("FORMat:DATA ASCII")
        self.Inst.write("INITiate:IMMediate;*wai")
        self.Inst.write("CALCulate:PARameter:SELect MySMeaS21")
        sawdata21 = self.Inst.query("CALCulate:DATA? SDATA")
        self.Inst.write("CALCulate:PARameter:SELect MySMeaS11")
        sawdata11 = self.Inst.query("CALCulate:DATA? SDATA")
        self.Inst.write("CALCulate:PARameter:SELect MySMeaS12")
        sawdata12 = self.Inst.query("CALCulate:DATA? SDATA")
        self.Inst.write("CALCulate:PARameter:SELect MySMeaS22")
        sawdata22 = self.Inst.query("CALCulate:DATA? SDATA")
        return (self.fixdata(sawdata21),
                self.fixdata(sawdata11),
                self.fixdata(sawdata12),
                self.fixdata(sawdata22))

    def Scan_freSpectrum(self, powers):
        S_data = list()
        f = None  # 原函数返回 (f, data)，但 f 未定义；保持语义尽量接近
        for i in range(len(powers)):
            self.set_power(powers[i])
            data = self.get_data()  # 原代码期望 get_data() 返回 (f, data)；此处按数据本身收集
            S_data.append(data)
            if len(powers) and i % max(1, int(len(powers) / 10)) == 0:
                print(f"scan_Fr: {(i + 1) / len(powers) * 100:.0f}% completed.")
        # 为兼容原签名，仍返回 (f, np.array(S_data))
        return f, np.array(S_data, dtype=object)

    def close(self):
        self.Inst.close()

    def two_tone_vna(self, channel=1):
        self.Inst.write("TRIGger:SEQuence:SOURce MANual")
        self.Inst.write("TRIG:SCOP CURRENT")
        if channel == 1:
            self.Inst.write(f"SENSe:SWEep:TRIGger:DELay {float(1) * 1e-3}")
            self.Inst.write("TRIG:CHAN:AUX2 0")
            self.Inst.write("TRIG:CHAN:AUX1 1")
            self.Inst.write("TRIG:CHAN:AUX1:OPOL POS")
            self.Inst.write("TRIG:CHAN:AUX1:POS AFT")
            self.Inst.write("TRIG:CHAN:AUX1:INTerval POINt")
            self.Inst.write("TRIG:CHAN:AUX1:DUR 10E-6")
        elif channel == 2:
            self.Inst.write(f"SENSe:SWEep:TRIGger:DELay {float(1) * 1e-3}")
            self.Inst.write("TRIG:CHAN:AUX1 0")
            self.Inst.write("TRIG:CHAN:AUX2 1")
            self.Inst.write("TRIG:CHAN:AUX2:OPOL POS")
            self.Inst.write("TRIG:CHAN:AUX2:POS AFT")
            self.Inst.write("TRIG:CHAN:AUX2:INTerval POINt")
            self.Inst.write("TRIG:CHAN:AUX2:DUR 10E-6")
        else:
            raise Exception("Channel must 1 and 2.")

    def poweroff(self, i):
        self.Inst.write(f"SOURce:POWer{int(i)}:MODE OFF")

    def SingleSweep(self):
        self.Inst.write("SENSe:SWEep:MODE Single")


# ---- 与原 wrapper 一致的便捷函数 ----
def vna_param_set(
    vna: KeysightVNA, trace: str, vnapwr: float, fstart: float, fstop: float,
    ifband: int, points: int, edelay=0, average=1,
):
    vna.trace(trace)          # 参数：选择 trace 方案
    vna.power(vnapwr)
    vna.fstart(fstart)
    vna.fstop(fstop)
    vna.ifband(ifband)
    vna.points(points)
    vna.electrical_delay(edelay)
    vna.average(average)


if __name__ == "__main__":
    from qcodes.instrument import find_or_create_instrument
    vna = find_or_create_instrument(KeysightVNA, "vna4port", "vna4port")
    vna.trace_param('S21')


    vna.power(-10)
    vna.fstart(6)
    vna.fstop(7)
    vna.points(101)
    vna.ifband(30)



    # data = vna.data()
    data = vna.average_sweep(5)

    print(data)

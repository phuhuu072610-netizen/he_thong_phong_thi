import argparse
import csv
import hashlib
import json
import os
import random
import secrets
import shutil
import tkinter as tk
from dataclasses import dataclass, asdict, field
from datetime import datetime, date, timedelta
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Optional, Tuple

FILE_DU_LIEU = "du_lieu_ca_thi.json"
MAT_KHAU_MAC_DINH = "admin123"

CHUA_NHAN = "Chưa nhận máy"
DA_NHAN = "Đã nhận máy"
DUOC_PHEP = "Được phép thi"
PHAM_QUY = "Phạm quy"

CA_CHUA_BAT_DAU = "Chưa bắt đầu"
CA_DANG_THI = "Đang thi"
CA_DA_KET_THUC = "Đã kết thúc"

DINH_DANG_NGAY = "%Y-%m-%d"
DINH_DANG_GIO = "%H:%M"

FONT = ("Arial", 12)
FONT_LON = ("Arial", 14)
FONT_TIEU_DE = ("Arial", 16, "bold")

MAU_TRONG = "#e5e7eb"
MAU_HONG = "#9ca3af"
MAU_CHON = "#2563eb"
MAU_TRANG_THAI = {
    DA_NHAN: "#fde68a",
    DUOC_PHEP: "#bbf7d0",
    PHAM_QUY: "#fca5a5",
}


def bay_gio() -> datetime:
    return datetime.now()


def thoi_gian_hien_tai() -> str:
    return bay_gio().strftime("%Y-%m-%d %H:%M:%S")


def ten_may(so_may: int) -> str:
    return f"Máy {so_may:02d}"


def hien_thi_ngay(chuoi: str) -> str:
    try:
        return datetime.strptime(chuoi, DINH_DANG_NGAY).strftime("%d/%m/%Y")
    except ValueError:
        return chuoi


def lay_mtime(duong_dan: str):
    try:
        return os.path.getmtime(duong_dan)
    except OSError:
        return None


@dataclass
class CaThi:
    ma_ca: str
    mon_thi: str
    ngay: str
    gio_bat_dau: str
    gio_ket_thuc: str
    phong: str
    so_may: int
    may_hong: List[int] = field(default_factory=list)

    def bat_dau(self) -> datetime:
        return datetime.strptime(f"{self.ngay} {self.gio_bat_dau}", f"{DINH_DANG_NGAY} {DINH_DANG_GIO}")

    def ket_thuc(self) -> datetime:
        return datetime.strptime(f"{self.ngay} {self.gio_ket_thuc}", f"{DINH_DANG_NGAY} {DINH_DANG_GIO}")

    def trang_thai(self, luc: Optional[datetime] = None) -> str:
        luc = luc or bay_gio()
        if luc < self.bat_dau():
            return CA_CHUA_BAT_DAU
        if luc <= self.ket_thuc():
            return CA_DANG_THI
        return CA_DA_KET_THUC

    def la_hom_nay(self) -> bool:
        return self.ngay == date.today().strftime(DINH_DANG_NGAY)


@dataclass
class SinhVien:
    mssv: str
    ho_ten: str


@dataclass
class DangKy:
    mssv: str
    ma_ca: str
    may: Optional[int] = None
    da_nhan_may: bool = False
    trang_thai: str = CHUA_NHAN
    ghi_chu: str = ""


LOC_DANH_SACH = {
    "Tất cả": lambda d: True,
    "Chưa nhận máy": lambda d: not d.da_nhan_may,
    "Đã nhận máy": lambda d: d.da_nhan_may,
    "Đã xác thực thành công": lambda d: d.trang_thai == DUOC_PHEP,
    "Vi phạm": lambda d: d.trang_thai == PHAM_QUY,
}


class HeThongCaThi:
    def __init__(self, file_du_lieu: str = FILE_DU_LIEU):
        self.file_du_lieu = file_du_lieu
        self.muoi: str = ""
        self.mat_khau_hash: str = ""
        self.ca_thi: Dict[str, CaThi] = {}
        self.sinh_vien: Dict[str, SinhVien] = {}
        self.dang_ky: List[DangKy] = []
        self.lich_su_cap_may: List[dict] = []
        self.lich_su_xac_thuc: List[dict] = []
        self.nhat_ky: List[dict] = []

        if os.path.exists(self.file_du_lieu):
            self.tai()
        else:
            self.khoi_tao_mau()
            self.luu()

    @staticmethod
    def _bam(mat_khau: str, muoi: str) -> str:
        return hashlib.sha256((muoi + mat_khau).encode("utf-8")).hexdigest()

    def luu(self) -> None:
        du_lieu = {
            "muoi": self.muoi,
            "mat_khau_hash": self.mat_khau_hash,
            "ca_thi": [asdict(c) for c in self.ca_thi.values()],
            "sinh_vien": [asdict(s) for s in self.sinh_vien.values()],
            "dang_ky": [asdict(d) for d in self.dang_ky],
            "lich_su_cap_may": self.lich_su_cap_may,
            "lich_su_xac_thuc": self.lich_su_xac_thuc,
            "nhat_ky": self.nhat_ky,
        }
        tam = self.file_du_lieu + ".tmp"
        with open(tam, "w", encoding="utf-8") as f:
            json.dump(du_lieu, f, ensure_ascii=False, indent=2)
        os.replace(tam, self.file_du_lieu)

    def tai(self) -> None:
        with open(self.file_du_lieu, "r", encoding="utf-8") as f:
            du_lieu = json.load(f)
        self.muoi = du_lieu["muoi"]
        self.mat_khau_hash = du_lieu["mat_khau_hash"]
        self.ca_thi = {c["ma_ca"]: CaThi(**c) for c in du_lieu["ca_thi"]}
        self.sinh_vien = {s["mssv"]: SinhVien(**s) for s in du_lieu["sinh_vien"]}
        self.dang_ky = [DangKy(**d) for d in du_lieu["dang_ky"]]
        self.lich_su_cap_may = du_lieu.get("lich_su_cap_may", [])
        self.lich_su_xac_thuc = du_lieu.get("lich_su_xac_thuc", [])
        self.nhat_ky = du_lieu.get("nhat_ky", [])

    def khoi_tao_mau(self) -> None:
        hom_nay = date.today()

        def ngay(lech: int) -> str:
            return (hom_nay + timedelta(days=lech)).strftime(DINH_DANG_NGAY)

        self.muoi = secrets.token_hex(8)
        self.mat_khau_hash = self._bam(MAT_KHAU_MAC_DINH, self.muoi)
        for ca in [
            CaThi("CA01", "Lập trình hướng đối tượng", ngay(0), "00:00", "23:59", "P.301", 10),
            CaThi("CA02", "Điện tử công nghiệp", ngay(0), "00:00", "23:59", "P.302", 8),
            CaThi("CA03", "Kỹ thuật điều khiển", ngay(1), "07:30", "09:30", "P.301", 10),
            CaThi("CA00", "Toán cao cấp", ngay(-1), "13:00", "15:00", "P.301", 10),
        ]:
            self.ca_thi[ca.ma_ca] = ca
        for mssv, ho_ten in [
            ("22800001", "Nguyễn Văn A"), ("22800002", "Trần Thị B"), ("22800003", "Lê Văn C"),
            ("22800004", "Phạm Thị D"), ("22800005", "Hoàng Văn E"), ("22800006", "Vũ Thị F"),
        ]:
            self.sinh_vien[mssv] = SinhVien(mssv, ho_ten)
        for mssv, cac_ca in [
            ("22800001", ["CA01", "CA02", "CA03", "CA00"]),
            ("22800002", ["CA01", "CA03"]),
            ("22800003", ["CA01"]),
            ("22800004", ["CA02"]),
            ("22800005", ["CA01", "CA02"]),
            ("22800006", ["CA03"]),
        ]:
            for ma_ca in cac_ca:
                self.dang_ky.append(DangKy(mssv, ma_ca))

    def ghi_nhat_ky(self, noi_dung: str) -> None:
        self.nhat_ky.append({"thoi_gian": thoi_gian_hien_tai(), "noi_dung": noi_dung})

    def kiem_tra_mat_khau(self, mat_khau: str) -> bool:
        self.tai()
        return secrets.compare_digest(self._bam(mat_khau, self.muoi), self.mat_khau_hash)

    def doi_mat_khau(self, mat_khau_moi: str) -> None:
        self.tai()
        self.muoi = secrets.token_hex(8)
        self.mat_khau_hash = self._bam(mat_khau_moi, self.muoi)
        self.ghi_nhat_ky("Đổi mật khẩu quản trị")
        self.luu()

    def tim_dang_ky(self, mssv: str, ma_ca: str) -> Optional[DangKy]:
        for d in self.dang_ky:
            if d.mssv == mssv and d.ma_ca == ma_ca:
                return d
        return None

    def ca_cua_sinh_vien(self, mssv: str) -> Optional[List[Tuple[CaThi, DangKy]]]:
        self.tai()
        mssv = mssv.strip()
        if mssv not in self.sinh_vien:
            return None
        ket_qua = [(self.ca_thi[d.ma_ca], d) for d in self.dang_ky
                   if d.mssv == mssv and d.ma_ca in self.ca_thi]
        ket_qua.sort(key=lambda x: (x[0].ngay, x[0].gio_bat_dau))
        return ket_qua

    def danh_sach_may_trong(self, ma_ca: str) -> List[int]:
        ca = self.ca_thi[ma_ca]
        da_cap = {d.may for d in self.dang_ky if d.ma_ca == ma_ca and d.may is not None}
        return [m for m in range(1, ca.so_may + 1) if m not in da_cap and m not in ca.may_hong]

    def _lay_dang_ky_hop_le(self, mssv: str, ma_ca: str):
        mssv = mssv.strip()
        sv = self.sinh_vien.get(mssv)
        ca = self.ca_thi.get(ma_ca)
        dk = self.tim_dang_ky(mssv, ma_ca)
        if sv is None or ca is None or dk is None:
            return None, None, None, "Sinh viên không thuộc ca thi này."
        if not ca.la_hom_nay():
            return None, None, None, "Chỉ được chọn ca thi diễn ra trong ngày hôm nay."
        if ca.trang_thai() == CA_DA_KET_THUC:
            return None, None, None, f"Ca thi {ca.ma_ca} đã kết thúc."
        return sv, ca, dk, None

    def cap_may(self, mssv: str, ma_ca: str) -> Tuple[bool, str]:
        self.tai()
        sv, ca, dk, loi = self._lay_dang_ky_hop_le(mssv, ma_ca)
        if loi:
            return False, loi

        if dk.da_nhan_may and dk.may is not None:
            return True, (f"Sinh viên {sv.ho_ten} – MSSV {sv.mssv} ĐÃ được cấp {ten_may(dk.may)} "
                          f"(ca {ca.ma_ca}, phòng {ca.phong}) trước đó. "
                          f"Vui lòng vào đúng {ten_may(dk.may)} để thi.")

        may_trong = self.danh_sach_may_trong(ma_ca)
        if not may_trong:
            return False, "Đã hết máy trống. Vui lòng liên hệ cán bộ coi thi."
        may_duoc_chon = random.choice(may_trong)

        dk.may = may_duoc_chon
        dk.da_nhan_may = True
        dk.trang_thai = DA_NHAN
        self.lich_su_cap_may.append({
            "mssv": sv.mssv, "ho_ten": sv.ho_ten, "ma_ca": ma_ca,
            "may": may_duoc_chon, "loai": "Cấp máy", "thoi_gian": thoi_gian_hien_tai(),
        })
        self.luu()
        return True, (f"Sinh viên {sv.ho_ten} – MSSV {sv.mssv} được cấp {ten_may(may_duoc_chon)} "
                      f"(ca {ca.ma_ca} – {ca.mon_thi}, phòng {ca.phong}). "
                      f"Vui lòng vào đúng {ten_may(may_duoc_chon)} để thi.")

    def xac_thuc(self, mssv: str, ma_ca: str, may_dang_dung: int) -> Tuple[bool, str]:
        self.tai()
        sv, ca, dk, loi = self._lay_dang_ky_hop_le(mssv, ma_ca)
        if loi:
            return False, loi
        if not dk.da_nhan_may or dk.may is None:
            return False, "Sinh viên chưa nhận máy. Vui lòng ra cửa phòng thi để được cấp máy."
        if dk.trang_thai == PHAM_QUY:
            return False, "Sinh viên đã bị ghi nhận PHẠM QUY – KHÔNG ĐƯỢC PHÉP THI."
        if not 1 <= may_dang_dung <= ca.so_may:
            return False, f"Mã máy không hợp lệ (phòng {ca.phong} có {ca.so_may} máy)."

        may_duoc_cap = dk.may
        mau_ghi = {
            "mssv": sv.mssv, "ho_ten": sv.ho_ten, "ma_ca": ma_ca,
            "may_duoc_cap": may_duoc_cap, "may_dang_nhap": may_dang_dung,
            "thoi_gian": thoi_gian_hien_tai(),
        }

        if may_duoc_cap == may_dang_dung:
            dk.trang_thai = DUOC_PHEP
            self.lich_su_xac_thuc.append({**mau_ghi, "ket_qua": "Thành công"})
            self.luu()
            return True, "Xác thực thành công. Sinh viên được phép bắt đầu bài thi."

        dk.trang_thai = PHAM_QUY
        self.lich_su_xac_thuc.append({**mau_ghi, "ket_qua": "Phạm quy"})
        self.luu()
        return False, ("CẢNH BÁO: Sinh viên không ngồi đúng máy được cấp.\n"
                       f"MSSV {sv.mssv} được cấp {ten_may(may_duoc_cap)} nhưng đang đăng nhập tại "
                       f"{ten_may(may_dang_dung)} → PHẠM QUY – KHÔNG ĐƯỢC PHÉP THI.")

    def thong_ke(self, ma_ca: str) -> dict:
        ca = self.ca_thi[ma_ca]
        ds = [d for d in self.dang_ky if d.ma_ca == ma_ca]
        return {
            "tong": len(ds),
            "da_nhan": sum(1 for d in ds if d.da_nhan_may),
            "xac_thuc": sum(1 for d in ds if d.trang_thai == DUOC_PHEP),
            "pham_quy": sum(1 for d in ds if d.trang_thai == PHAM_QUY),
            "chua_nhan": sum(1 for d in ds if not d.da_nhan_may),
            "may_trong": len(self.danh_sach_may_trong(ma_ca)),
            "may_hong": len(ca.may_hong),
            "so_may": ca.so_may,
        }

    def ds_dang_ky(self, ma_ca: str, loc: str = "Tất cả", tu_khoa: str = "") -> List[Tuple[SinhVien, DangKy]]:
        ham = LOC_DANH_SACH.get(loc, LOC_DANH_SACH["Tất cả"])
        tu_khoa = tu_khoa.strip().lower()
        ket_qua = []
        for d in self.dang_ky:
            if d.ma_ca != ma_ca or not ham(d):
                continue
            sv = self.sinh_vien.get(d.mssv)
            if sv is None:
                continue
            if tu_khoa and tu_khoa not in sv.mssv.lower() and tu_khoa not in sv.ho_ten.lower():
                continue
            ket_qua.append((sv, d))
        ket_qua.sort(key=lambda x: x[0].mssv)
        return ket_qua

    def doi_may(self, mssv: str, ma_ca: str) -> Tuple[bool, str]:
        self.tai()
        mssv = mssv.strip()
        dk = self.tim_dang_ky(mssv, ma_ca)
        ca = self.ca_thi.get(ma_ca)
        if dk is None or ca is None:
            return False, "Sinh viên không thuộc ca thi này."
        if not dk.da_nhan_may or dk.may is None:
            return False, "Sinh viên chưa được cấp máy, không cần đổi."

        may_trong = self.danh_sach_may_trong(ma_ca)
        if not may_trong:
            return False, "Không còn máy trống để đổi."

        may_cu = dk.may
        may_moi = random.choice(may_trong)
        if may_cu not in ca.may_hong:
            ca.may_hong.append(may_cu)
        dk.may = may_moi
        dk.trang_thai = DA_NHAN
        sv = self.sinh_vien[mssv]
        self.lich_su_cap_may.append({
            "mssv": mssv, "ho_ten": sv.ho_ten, "ma_ca": ma_ca, "may": may_moi,
            "loai": f"Đổi máy (từ {ten_may(may_cu)} bị hỏng)", "thoi_gian": thoi_gian_hien_tai(),
        })
        self.ghi_nhat_ky(f"Đổi máy cho {mssv} (ca {ma_ca}): {ten_may(may_cu)} → {ten_may(may_moi)}")
        self.luu()
        return True, (f"Đã đổi {sv.ho_ten} – MSSV {mssv} từ {ten_may(may_cu)} (hỏng) "
                      f"sang {ten_may(may_moi)}. Sinh viên cần xác thực lại.")

    def xu_ly_pham_quy(self, mssv: str, ma_ca: str, ly_do: str) -> Tuple[bool, str]:
        self.tai()
        dk = self.tim_dang_ky(mssv.strip(), ma_ca)
        if dk is None:
            return False, "Sinh viên không thuộc ca thi này."
        if dk.trang_thai != PHAM_QUY:
            return False, "Sinh viên này không ở trạng thái Phạm quy."
        if not ly_do.strip():
            return False, "Vui lòng nhập lý do xử lý."
        dk.trang_thai = DA_NHAN
        dk.ghi_chu = f"Đã gỡ phạm quy lúc {thoi_gian_hien_tai()}: {ly_do.strip()}"
        self.ghi_nhat_ky(f"Gỡ phạm quy cho {mssv} (ca {ma_ca}). Lý do: {ly_do.strip()}")
        self.luu()
        return True, "Đã gỡ phạm quy. Sinh viên cần xác thực lại tại đúng máy được cấp."

    def danh_dau_may_hong(self, ma_ca: str, so_may: int, hong: bool) -> Tuple[bool, str]:
        self.tai()
        ca = self.ca_thi.get(ma_ca)
        if ca is None or not 1 <= so_may <= ca.so_may:
            return False, "Máy không hợp lệ."
        if hong:
            if so_may in ca.may_hong:
                return False, f"{ten_may(so_may)} đã được đánh dấu hỏng."
            chu = next((d for d in self.dang_ky if d.ma_ca == ma_ca and d.may == so_may), None)
            if chu:
                return False, (f"{ten_may(so_may)} đang được cấp cho MSSV {chu.mssv}. "
                               "Hãy dùng chức năng Đổi máy trong tab Danh sách.")
            ca.may_hong.append(so_may)
            self.ghi_nhat_ky(f"Đánh dấu {ten_may(so_may)} hỏng (ca {ma_ca})")
            self.luu()
            return True, f"Đã đánh dấu {ten_may(so_may)} hỏng."
        if so_may not in ca.may_hong:
            return False, f"{ten_may(so_may)} chưa bị đánh dấu hỏng."
        ca.may_hong.remove(so_may)
        self.ghi_nhat_ky(f"Bỏ đánh dấu hỏng {ten_may(so_may)} (ca {ma_ca})")
        self.luu()
        return True, f"Đã bỏ đánh dấu hỏng {ten_may(so_may)}."

    def _kiem_tra_thong_tin_ca(self, mon_thi, ngay, gio_bd, gio_kt, phong, so_may):
        if not mon_thi:
            return "Vui lòng nhập tên môn thi.", None, None, None, None
        try:
            ngay = datetime.strptime(ngay, DINH_DANG_NGAY).strftime(DINH_DANG_NGAY)
        except ValueError:
            return "Ngày thi không hợp lệ (định dạng YYYY-MM-DD, ví dụ 2026-11-12).", None, None, None, None
        try:
            bd = datetime.strptime(gio_bd, DINH_DANG_GIO)
            kt = datetime.strptime(gio_kt, DINH_DANG_GIO)
        except ValueError:
            return "Giờ không hợp lệ (định dạng HH:MM, ví dụ 07:30).", None, None, None, None
        if kt <= bd:
            return "Giờ kết thúc phải sau giờ bắt đầu.", None, None, None, None
        if not phong:
            return "Vui lòng nhập phòng thi.", None, None, None, None
        try:
            n = int(so_may)
        except ValueError:
            return "Số máy phải là số nguyên.", None, None, None, None
        if not 1 <= n <= 500:
            return "Số máy phải từ 1 đến 500.", None, None, None, None
        return None, ngay, bd.strftime(DINH_DANG_GIO), kt.strftime(DINH_DANG_GIO), n

    def them_ca(self, ma_ca, mon_thi, ngay, gio_bd, gio_kt, phong, so_may) -> Tuple[bool, str]:
        self.tai()
        ma_ca = ma_ca.strip().upper()
        if not ma_ca:
            return False, "Vui lòng nhập mã ca thi."
        if ma_ca in self.ca_thi:
            return False, f"Mã ca {ma_ca} đã tồn tại."
        loi, ngay, gbd, gkt, n = self._kiem_tra_thong_tin_ca(
            mon_thi.strip(), ngay.strip(), gio_bd.strip(), gio_kt.strip(), phong.strip(), so_may.strip())
        if loi:
            return False, loi
        self.ca_thi[ma_ca] = CaThi(ma_ca, mon_thi.strip(), ngay, gbd, gkt, phong.strip(), n)
        self.ghi_nhat_ky(f"Thêm ca thi {ma_ca} – {mon_thi.strip()}")
        self.luu()
        return True, f"Đã thêm ca thi {ma_ca}."

    def sua_ca(self, ma_ca, mon_thi, ngay, gio_bd, gio_kt, phong, so_may) -> Tuple[bool, str]:
        self.tai()
        ca = self.ca_thi.get(ma_ca)
        if ca is None:
            return False, "Không tìm thấy ca thi."
        loi, ngay, gbd, gkt, n = self._kiem_tra_thong_tin_ca(
            mon_thi.strip(), ngay.strip(), gio_bd.strip(), gio_kt.strip(), phong.strip(), so_may.strip())
        if loi:
            return False, loi
        may_lon_nhat = max([d.may for d in self.dang_ky if d.ma_ca == ma_ca and d.may], default=0)
        if n < may_lon_nhat:
            return False, f"Không thể giảm số máy xuống {n} vì {ten_may(may_lon_nhat)} đã được cấp cho sinh viên."
        ca.mon_thi, ca.ngay, ca.gio_bat_dau, ca.gio_ket_thuc = mon_thi.strip(), ngay, gbd, gkt
        ca.phong, ca.so_may = phong.strip(), n
        ca.may_hong = [m for m in ca.may_hong if m <= n]
        self.ghi_nhat_ky(f"Sửa thông tin ca thi {ma_ca}")
        self.luu()
        return True, f"Đã cập nhật ca thi {ma_ca}."

    def xoa_ca(self, ma_ca: str) -> Tuple[bool, str]:
        self.tai()
        if ma_ca not in self.ca_thi:
            return False, "Không tìm thấy ca thi."
        del self.ca_thi[ma_ca]
        self.dang_ky = [d for d in self.dang_ky if d.ma_ca != ma_ca]
        self.ghi_nhat_ky(f"Xóa ca thi {ma_ca} cùng toàn bộ đăng ký của ca")
        self.luu()
        return True, f"Đã xóa ca thi {ma_ca}."

    def them_sinh_vien_vao_ca(self, mssv: str, ho_ten: str, ma_ca: str) -> Tuple[bool, str]:
        self.tai()
        mssv, ho_ten = mssv.strip(), ho_ten.strip()
        if not mssv:
            return False, "Vui lòng nhập MSSV."
        if ma_ca not in self.ca_thi:
            return False, "Vui lòng chọn ca thi hợp lệ."
        if mssv not in self.sinh_vien:
            if not ho_ten:
                return False, "MSSV mới, vui lòng nhập họ tên."
            self.sinh_vien[mssv] = SinhVien(mssv, ho_ten)
        if self.tim_dang_ky(mssv, ma_ca):
            return False, "Sinh viên đã có trong ca thi này."
        self.dang_ky.append(DangKy(mssv, ma_ca))
        self.ghi_nhat_ky(f"Thêm {mssv} – {self.sinh_vien[mssv].ho_ten} vào ca {ma_ca}")
        self.luu()
        return True, f"Đã thêm {self.sinh_vien[mssv].ho_ten} vào ca {ma_ca}."

    def xoa_dang_ky(self, mssv: str, ma_ca: str) -> Tuple[bool, str]:
        self.tai()
        dk = self.tim_dang_ky(mssv, ma_ca)
        if dk is None:
            return False, "Không tìm thấy đăng ký."
        self.dang_ky.remove(dk)
        self.ghi_nhat_ky(f"Xóa {mssv} khỏi ca {ma_ca}")
        self.luu()
        return True, f"Đã xóa MSSV {mssv} khỏi ca {ma_ca}."

    def import_csv(self, duong_dan: str) -> Tuple[bool, str]:
        if not os.path.exists(duong_dan):
            return False, "Không tìm thấy file CSV."
        self.tai()
        them = trung = loi = 0
        with open(duong_dan, "r", encoding="utf-8-sig", newline="") as f:
            for dong in csv.DictReader(f):
                mssv = (dong.get("mssv") or "").strip()
                ho_ten = (dong.get("ho_ten") or "").strip()
                ma_ca = (dong.get("ma_ca") or "").strip().upper()
                if not mssv or ma_ca not in self.ca_thi:
                    loi += 1
                    continue
                if mssv not in self.sinh_vien:
                    if not ho_ten:
                        loi += 1
                        continue
                    self.sinh_vien[mssv] = SinhVien(mssv, ho_ten)
                if self.tim_dang_ky(mssv, ma_ca):
                    trung += 1
                    continue
                self.dang_ky.append(DangKy(mssv, ma_ca))
                them += 1
        self.ghi_nhat_ky(f"Import CSV: thêm {them}, trùng {trung}, lỗi {loi}")
        self.luu()
        return True, f"Đã thêm {them} đăng ký. Bỏ qua {trung} dòng trùng và {loi} dòng lỗi (thiếu MSSV/họ tên hoặc mã ca không tồn tại)."

    def export_phan_may_csv(self, duong_dan: str, ma_ca: str) -> str:
        self.tai()
        ca = self.ca_thi[ma_ca]
        with open(duong_dan, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["MSSV", "Họ tên", "Mã ca", "Môn thi", "Ngày", "Phòng", "Máy được cấp", "Trạng thái", "Ghi chú"])
            for sv, d in self.ds_dang_ky(ma_ca):
                w.writerow([sv.mssv, sv.ho_ten, ca.ma_ca, ca.mon_thi, hien_thi_ngay(ca.ngay), ca.phong,
                            ten_may(d.may) if d.may else "", d.trang_thai, d.ghi_chu])
        return f"Đã xuất kết quả phân máy ca {ma_ca} ra file: {duong_dan}"

    def _ds_vi_pham(self, ma_ca: str) -> List[dict]:
        return [b for b in self.lich_su_xac_thuc if b["ma_ca"] == ma_ca and b["ket_qua"] == "Phạm quy"]

    def export_vi_pham_csv(self, duong_dan: str, ma_ca: str) -> str:
        self.tai()
        with open(duong_dan, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["MSSV", "Họ tên", "Mã ca", "Máy được cấp", "Máy đang đăng nhập", "Thời gian vi phạm"])
            for b in self._ds_vi_pham(ma_ca):
                w.writerow([b["mssv"], b["ho_ten"], ma_ca, ten_may(b["may_duoc_cap"]),
                            ten_may(b["may_dang_nhap"]), b["thoi_gian"]])
        return f"Đã xuất danh sách vi phạm ca {ma_ca} ra file: {duong_dan}"

    def export_bien_ban_txt(self, duong_dan: str, ma_ca: str) -> str:
        self.tai()
        ca = self.ca_thi[ma_ca]
        ds = self._ds_vi_pham(ma_ca)
        dong = [
            "BIÊN BẢN VI PHẠM QUY CHẾ THI",
            "=" * 60,
            f"Ca thi: {ca.ma_ca} – {ca.mon_thi}",
            f"Ngày thi: {hien_thi_ngay(ca.ngay)}   Giờ: {ca.gio_bat_dau} – {ca.gio_ket_thuc}   Phòng: {ca.phong}",
            f"Thời gian lập biên bản: {thoi_gian_hien_tai()}",
            f"Số trường hợp vi phạm: {len(ds)}",
            "",
        ]
        for i, b in enumerate(ds, 1):
            dong += [
                f"{i}. MSSV {b['mssv']} – {b['ho_ten']}",
                f"   Máy được cấp: {ten_may(b['may_duoc_cap'])}",
                f"   Máy đang đăng nhập: {ten_may(b['may_dang_nhap'])}",
                f"   Thời gian phát hiện: {b['thoi_gian']}",
                "   Hình thức xử lý: Không được phép thi (ngồi sai máy được cấp)",
                "",
            ]
        dong += ["", "Cán bộ coi thi 1: ____________________    Cán bộ coi thi 2: ____________________"]
        with open(duong_dan, "w", encoding="utf-8") as f:
            f.write("\n".join(dong))
        return f"Đã xuất biên bản vi phạm ca {ma_ca} ra file: {duong_dan}"

    def sao_luu(self, duong_dan: str) -> str:
        self.tai()
        shutil.copyfile(self.file_du_lieu, duong_dan)
        return f"Đã sao lưu dữ liệu ra file: {duong_dan}"

    def khoi_phuc(self, duong_dan: str) -> Tuple[bool, str]:
        try:
            with open(duong_dan, "r", encoding="utf-8") as f:
                du_lieu = json.load(f)
            for khoa in ("muoi", "mat_khau_hash", "ca_thi", "sinh_vien", "dang_ky"):
                if khoa not in du_lieu:
                    return False, "File sao lưu không đúng định dạng của hệ thống."
        except (OSError, ValueError):
            return False, "Không đọc được file sao lưu."
        shutil.copyfile(duong_dan, self.file_du_lieu)
        self.tai()
        self.ghi_nhat_ky("Khôi phục dữ liệu từ file sao lưu")
        self.luu()
        return True, "Đã khôi phục dữ liệu từ file sao lưu."

    def dat_lai_phan_may(self, ma_ca: str) -> Tuple[bool, str]:
        self.tai()
        if ma_ca not in self.ca_thi:
            return False, "Không tìm thấy ca thi."
        for d in self.dang_ky:
            if d.ma_ca == ma_ca:
                d.may, d.da_nhan_may, d.trang_thai, d.ghi_chu = None, False, CHUA_NHAN, ""
        self.ghi_nhat_ky(f"Đặt lại toàn bộ phân máy của ca {ma_ca}")
        self.luu()
        return True, f"Đã đặt lại phân máy của ca {ma_ca}."


def tao_bang(cha, cot, chieu_cao=10):
    khung = ttk.Frame(cha)
    bang = ttk.Treeview(khung, columns=[c[0] for c in cot], show="headings",
                        height=chieu_cao, selectmode="browse")
    for ten, rong in cot:
        bang.heading(ten, text=ten)
        bang.column(ten, width=rong, anchor="w")
    thanh_cuon = ttk.Scrollbar(khung, orient="vertical", command=bang.yview)
    bang.configure(yscrollcommand=thanh_cuon.set)
    bang.pack(side="left", fill="both", expand=True)
    thanh_cuon.pack(side="right", fill="y")
    return khung, bang


def dien_bang(bang, hang, iid_ds=None):
    truoc = bang.selection()
    bang.delete(*bang.get_children())
    for i, h in enumerate(hang):
        bang.insert("", "end", iid=iid_ds[i] if iid_ds else None, values=h)
    for iid in truoc:
        if bang.exists(iid):
            bang.selection_add(iid)


class HopThoaiForm(tk.Toplevel):
    def __init__(self, cha, tieu_de, cac_truong, nut_ok="Lưu"):
        super().__init__(cha)
        self.title(tieu_de)
        self.transient(cha)
        self.resizable(False, False)
        self.ket_qua = None
        self.cac_bien = {}

        khung = ttk.Frame(self, padding=16)
        khung.pack(fill="both", expand=True)
        for i, (khoa, nhan, mac_dinh, lua_chon) in enumerate(cac_truong):
            ttk.Label(khung, text=nhan, font=FONT).grid(row=i, column=0, sticky="w", padx=(0, 10), pady=5)
            bien = tk.StringVar(value=str(mac_dinh))
            if lua_chon == "*":
                o = ttk.Entry(khung, textvariable=bien, width=40, font=FONT, show="*")
            elif lua_chon:
                o = ttk.Combobox(khung, textvariable=bien, values=lua_chon, state="readonly", width=38, font=FONT)
            else:
                o = ttk.Entry(khung, textvariable=bien, width=40, font=FONT)
            o.grid(row=i, column=1, pady=5)
            self.cac_bien[khoa] = bien
            if i == 0:
                o.focus_set()

        hang = ttk.Frame(khung)
        hang.grid(row=len(cac_truong), column=0, columnspan=2, pady=(14, 0))
        ttk.Button(hang, text=nut_ok, command=self.dong_y).pack(side="left", padx=6)
        ttk.Button(hang, text="Hủy", command=self.destroy).pack(side="left", padx=6)
        self.bind("<Return>", lambda e: self.dong_y())
        self.bind("<Escape>", lambda e: self.destroy())
        self.grab_set()
        self.wait_window(self)

    def dong_y(self):
        self.ket_qua = {k: v.get().strip() for k, v in self.cac_bien.items()}
        self.destroy()


class BangChonCa(ttk.Frame):
    def __init__(self, cha, he_thong, ten_nut, hanh_dong, hien_o_may=False, may_co_dinh=None):
        super().__init__(cha, padding=14)
        self.ht = he_thong
        self.hanh_dong = hanh_dong
        self.hien_o_may = hien_o_may
        self.may_co_dinh = may_co_dinh
        self.mssv_hien_tai = None
        self.cac_ca = {}

        hang = ttk.Frame(self)
        hang.pack(fill="x")
        ttk.Label(hang, text="Mã số sinh viên:", font=FONT).pack(side="left", padx=(0, 6))
        self.var_mssv = tk.StringVar()
        o_nhap = ttk.Entry(hang, textvariable=self.var_mssv, font=FONT, width=22)
        o_nhap.pack(side="left", padx=6)
        o_nhap.bind("<Return>", lambda e: self.tim_ca())
        ttk.Button(hang, text="Xem ca thi của tôi", command=self.tim_ca).pack(side="left", padx=6)

        self.lbl_sv = ttk.Label(self, text="", font=("Arial", 12, "bold"))
        self.lbl_sv.pack(anchor="w", pady=(10, 2))
        ttk.Label(self, text="Chỉ chọn được ca thi diễn ra trong ngày hôm nay (dòng nền xanh).",
                  foreground="#6b7280").pack(anchor="w", pady=(0, 6))

        khung_bang, self.bang = tao_bang(self, [
            ("Mã ca", 70), ("Môn thi", 210), ("Ngày", 90), ("Giờ thi", 110),
            ("Phòng", 70), ("Trạng thái ca", 110), ("Máy được cấp", 100), ("Trạng thái", 110),
        ], chieu_cao=7)
        khung_bang.pack(fill="both", expand=True)
        self.bang.tag_configure("hom_nay", background="#dcfce7")
        self.bang.tag_configure("khac_ngay", foreground="#9ca3af")
        self.bang.bind("<<TreeviewSelect>>", self.khi_chon)

        hang2 = ttk.Frame(self)
        hang2.pack(pady=12)
        self.cb_may = None
        if hien_o_may:
            ttk.Label(hang2, text="Máy đang sử dụng (máy số):", font=FONT).pack(side="left", padx=6)
            self.var_may = tk.StringVar(value=str(may_co_dinh) if may_co_dinh else "1")
            self.cb_may = ttk.Combobox(hang2, textvariable=self.var_may, width=6, font=FONT,
                                       state="disabled" if may_co_dinh else "readonly")
            self.cb_may.pack(side="left", padx=6)
        self.nut = ttk.Button(hang2, text=ten_nut, command=self.thuc_hien, state="disabled")
        self.nut.pack(side="left", padx=10)

        self.lbl_kq = tk.Label(self, text="", font=FONT_LON, wraplength=860, justify="center", pady=16)
        self.lbl_kq.pack(fill="x")
        self.mau_nen_mac_dinh = self.lbl_kq.cget("bg")
        self.mau_chu_mac_dinh = self.lbl_kq.cget("fg")

    def hien_ket_qua(self, thanh_cong, noi_dung):
        if thanh_cong:
            self.lbl_kq.config(text=noi_dung, bg="#bbf7d0", fg="#14532d")
        else:
            self.lbl_kq.config(text=noi_dung, bg="#fca5a5", fg="#7f1d1d")

    def dat_lai(self):
        self.var_mssv.set("")
        self.mssv_hien_tai = None
        self.cac_ca = {}
        self.bang.delete(*self.bang.get_children())
        self.lbl_sv.config(text="")
        self.lbl_kq.config(text="", bg=self.mau_nen_mac_dinh, fg=self.mau_chu_mac_dinh)
        self.nut.config(state="disabled")

    def tim_ca(self):
        mssv = self.var_mssv.get().strip()
        if not mssv:
            messagebox.showinfo("Thiếu thông tin", "Vui lòng nhập mã số sinh viên.")
            return
        ds = self.ht.ca_cua_sinh_vien(mssv)
        self.bang.delete(*self.bang.get_children())
        self.cac_ca = {}
        self.nut.config(state="disabled")
        if ds is None:
            self.mssv_hien_tai = None
            self.lbl_sv.config(text="")
            self.hien_ket_qua(False, "Mã số sinh viên không tồn tại trong hệ thống.")
            return
        self.mssv_hien_tai = mssv
        self.lbl_sv.config(text=f"Sinh viên: {self.ht.sinh_vien[mssv].ho_ten} – MSSV {mssv}")
        self.lbl_kq.config(text="", bg=self.mau_nen_mac_dinh, fg=self.mau_chu_mac_dinh)
        if not ds:
            self.hien_ket_qua(False, "Sinh viên chưa có ca thi nào.")
            return
        self.do_bang(ds)

    def do_bang(self, ds):
        for ca, dk in ds:
            self.cac_ca[ca.ma_ca] = (ca, dk)
            self.bang.insert("", "end", iid=ca.ma_ca, tags=("hom_nay" if ca.la_hom_nay() else "khac_ngay",), values=(
                ca.ma_ca, ca.mon_thi, hien_thi_ngay(ca.ngay), f"{ca.gio_bat_dau} – {ca.gio_ket_thuc}",
                ca.phong, ca.trang_thai(), ten_may(dk.may) if dk.may else "-", dk.trang_thai,
            ))

    def lam_moi_bang(self, giu_chon=None):
        ds = self.ht.ca_cua_sinh_vien(self.mssv_hien_tai) if self.mssv_hien_tai else None
        self.bang.delete(*self.bang.get_children())
        self.cac_ca = {}
        if ds:
            self.do_bang(ds)
            if giu_chon and self.bang.exists(giu_chon):
                self.bang.selection_set(giu_chon)

    def khi_chon(self, _event=None):
        chon = self.bang.selection()
        if not chon:
            self.nut.config(state="disabled")
            return
        ca, _dk = self.cac_ca[chon[0]]
        if not ca.la_hom_nay():
            self.bang.selection_remove(chon)
            self.nut.config(state="disabled")
            messagebox.showwarning(
                "Không thể chọn ca thi này",
                f"Ca {ca.ma_ca} diễn ra ngày {hien_thi_ngay(ca.ngay)}, không phải hôm nay.\n"
                "Chỉ được chọn ca thi diễn ra trong ngày hôm nay.")
            return
        self.nut.config(state="normal")
        if self.cb_may is not None and not self.may_co_dinh:
            self.cb_may["values"] = list(range(1, ca.so_may + 1))
            if not self.var_may.get().isdigit() or not 1 <= int(self.var_may.get()) <= ca.so_may:
                self.var_may.set("1")

    def thuc_hien(self):
        chon = self.bang.selection()
        if not chon or not self.mssv_hien_tai:
            return
        ma_ca = chon[0]
        if self.hien_o_may:
            try:
                so_may = int(self.var_may.get())
            except ValueError:
                messagebox.showerror("Lỗi", "Số máy không hợp lệ.")
                return
            thanh_cong, noi_dung = self.hanh_dong(self.mssv_hien_tai, ma_ca, so_may)
        else:
            thanh_cong, noi_dung = self.hanh_dong(self.mssv_hien_tai, ma_ca)
        self.hien_ket_qua(thanh_cong, noi_dung)
        if noi_dung.startswith("CẢNH BÁO"):
            self.bell()
            messagebox.showwarning("PHẠM QUY", noi_dung)
        self.lam_moi_bang(giu_chon=ma_ca)


class ManHinhChinh(ttk.Frame):
    def __init__(self, cha, ung_dung):
        super().__init__(cha)
        giua = ttk.Frame(self)
        giua.place(relx=0.5, rely=0.45, anchor="center")
        ttk.Label(giua, text="HỆ THỐNG QUẢN LÝ CA THI", font=("Arial", 26, "bold")).pack(pady=(0, 6))
        ttk.Label(giua, text="Cấp máy ngẫu nhiên và xác thực thí sinh trong phòng thi",
                  font=FONT_LON).pack(pady=(0, 34))
        ttk.Button(giua, text="Giao diện sinh viên", style="Lon.TButton", width=36,
                   command=ung_dung.vao_sinh_vien).pack(pady=8)
        ttk.Button(giua, text="Giao diện giáo viên / cán bộ coi thi", style="Lon.TButton", width=36,
                   command=ung_dung.vao_giao_vien).pack(pady=8)
        ttk.Button(giua, text="Thoát", style="Lon.TButton", width=36,
                   command=ung_dung.destroy).pack(pady=8)


class GiaoDienSinhVien(ttk.Frame):
    def __init__(self, cha, ht, may_co_dinh=None):
        super().__init__(cha)
        self.so_tab = ttk.Notebook(self)
        self.so_tab.pack(fill="both", expand=True, padx=10, pady=10)
        self.bang_nhan = BangChonCa(self.so_tab, ht, "Nhận máy", ht.cap_may)
        self.bang_xt = BangChonCa(self.so_tab, ht, "Xác thực", ht.xac_thuc,
                                  hien_o_may=True, may_co_dinh=may_co_dinh)
        self.so_tab.add(self.bang_nhan, text="Nhận máy (tại cửa phòng thi)")
        self.so_tab.add(self.bang_xt, text="Xác thực (tại máy thi)")

    def dat_lai(self):
        self.bang_nhan.dat_lai()
        self.bang_xt.dat_lai()
        self.so_tab.select(0)


class GiaoDienGiaoVien(ttk.Frame):
    def __init__(self, cha, ht):
        super().__init__(cha)
        self.ht = ht
        self.nhan_ca = {}
        self.mtime_cu = None
        self.may_chon = None
        self.var_loc = tk.StringVar(value="Tất cả")
        self.var_tim = tk.StringVar()
        self.var_tim_sv = tk.StringVar()

        thanh = ttk.Frame(self, padding=(10, 8))
        thanh.pack(fill="x")
        ttk.Label(thanh, text="Ca đang quản lý:", font=FONT).pack(side="left")
        self.cb_ca = ttk.Combobox(thanh, state="readonly", width=64, font=FONT)
        self.cb_ca.pack(side="left", padx=8)
        self.cb_ca.bind("<<ComboboxSelected>>", lambda e: self.lam_moi_noi_dung())
        self.lbl_trang_thai_ca = ttk.Label(thanh, font=("Arial", 11, "bold"))
        self.lbl_trang_thai_ca.pack(side="left", padx=10)

        self.so_tab = ttk.Notebook(self)
        self.so_tab.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.xay_tab_tong_quan()
        self.xay_tab_so_do()
        self.xay_tab_danh_sach()
        self.xay_tab_ca_thi()
        self.xay_tab_sinh_vien()
        self.xay_tab_lich_su()
        self.xay_tab_bao_cao()

    def ma_ca(self):
        return self.nhan_ca.get(self.cb_ca.get())

    def hop_thoai(self, tieu_de, cac_truong, nut_ok="Lưu"):
        return HopThoaiForm(self.winfo_toplevel(), tieu_de, cac_truong, nut_ok).ket_qua

    def thong_bao(self, thanh_cong, noi_dung, tieu_de="Kết quả"):
        (messagebox.showinfo if thanh_cong else messagebox.showwarning)(tieu_de, noi_dung)

    def xay_tab_tong_quan(self):
        khung = ttk.Frame(self.so_tab, padding=20)
        self.so_tab.add(khung, text="Tổng quan")
        ttk.Label(khung, text="THỐNG KÊ CA THI", font=FONT_TIEU_DE).pack(pady=(0, 16))

        luoi = ttk.Frame(khung)
        luoi.pack()
        self.the_so = {}
        cac_the = [
            ("tong", "Tổng số sinh viên", "#dbeafe"), ("da_nhan", "Đã nhận máy", "#fde68a"),
            ("xac_thuc", "Đã xác thực", "#bbf7d0"), ("pham_quy", "Phạm quy", "#fca5a5"),
            ("chua_nhan", "Chưa nhận máy / vắng", "#e5e7eb"), ("may_trong", "Máy còn trống", "#e0f2fe"),
            ("may_hong", "Máy hỏng", "#d1d5db"), ("so_may", "Tổng số máy", "#ede9fe"),
        ]
        for i, (khoa, nhan, mau) in enumerate(cac_the):
            the = tk.Frame(luoi, bg=mau, bd=1, relief="ridge", padx=14, pady=12)
            the.grid(row=i // 4, column=i % 4, padx=8, pady=8, sticky="nsew")
            lbl_so = tk.Label(the, text="0", font=("Arial", 28, "bold"), bg=mau, width=5)
            lbl_so.pack()
            tk.Label(the, text=nhan, font=("Arial", 10), bg=mau).pack()
            self.the_so[khoa] = lbl_so

        ttk.Label(khung, text="Tiến độ nhận máy", font=FONT).pack(pady=(22, 4))
        self.thanh_tien_do = ttk.Progressbar(khung, length=520, maximum=100)
        self.thanh_tien_do.pack()
        self.lbl_ty_le = ttk.Label(khung, text="", font=FONT)
        self.lbl_ty_le.pack(pady=6)

    def ve_tong_quan(self, ma_ca):
        tk_ = self.ht.thong_ke(ma_ca)
        for khoa, lbl in self.the_so.items():
            lbl.config(text=str(tk_[khoa]))
        ty_le = 100 * tk_["da_nhan"] / tk_["tong"] if tk_["tong"] else 0
        self.thanh_tien_do["value"] = ty_le
        self.lbl_ty_le.config(text=f"{tk_['da_nhan']}/{tk_['tong']} sinh viên đã nhận máy ({ty_le:.0f}%)")

    def xay_tab_so_do(self):
        khung = ttk.Frame(self.so_tab, padding=10)
        self.so_tab.add(khung, text="Sơ đồ máy")

        chu_thich = ttk.Frame(khung)
        chu_thich.pack(fill="x", pady=(0, 8))
        for nhan, mau in [("Trống", MAU_TRONG), ("Đã nhận máy", MAU_TRANG_THAI[DA_NHAN]),
                          ("Được phép thi", MAU_TRANG_THAI[DUOC_PHEP]),
                          ("Phạm quy", MAU_TRANG_THAI[PHAM_QUY]), ("Máy hỏng", MAU_HONG)]:
            tk.Label(chu_thich, text=nhan, bg=mau, width=14, relief="ridge").pack(side="left", padx=4)

        hang = ttk.Frame(khung)
        hang.pack(fill="x", pady=(0, 8))
        self.lbl_may_chon = ttk.Label(hang, text="Nhấn vào một máy để chọn.", font=FONT)
        self.lbl_may_chon.pack(side="left")
        ttk.Button(hang, text="Bỏ đánh dấu hỏng", command=lambda: self.dat_may_hong(False)).pack(side="right", padx=4)
        ttk.Button(hang, text="Đánh dấu máy hỏng", command=lambda: self.dat_may_hong(True)).pack(side="right", padx=4)

        self.khung_may = ttk.Frame(khung)
        self.khung_may.pack(fill="both", expand=True)

    def chon_may(self, so_may):
        self.may_chon = so_may
        self.ve_so_do(self.ma_ca())

    def ve_so_do(self, ma_ca):
        for w in self.khung_may.winfo_children():
            w.destroy()
        ca = self.ht.ca_thi[ma_ca]
        theo_may = {d.may: d for d in self.ht.dang_ky if d.ma_ca == ma_ca and d.may is not None}
        so_cot = 5
        for c in range(so_cot):
            self.khung_may.columnconfigure(c, weight=1)
        if self.may_chon is not None and self.may_chon > ca.so_may:
            self.may_chon = None
        for m in range(1, ca.so_may + 1):
            if m in ca.may_hong:
                mau, mo_ta = MAU_HONG, "HỎNG"
            elif m in theo_may:
                d = theo_may[m]
                mau = MAU_TRANG_THAI.get(d.trang_thai, MAU_TRONG)
                mo_ta = f"{d.mssv}\n{d.trang_thai}"
            else:
                mau, mo_ta = MAU_TRONG, "(trống)"
            da_chon = m == self.may_chon
            o = tk.Label(self.khung_may, text=f"{ten_may(m)}\n{mo_ta}", bg=mau, font=("Arial", 10),
                         height=4, relief="solid" if da_chon else "ridge", bd=4 if da_chon else 2,
                         highlightbackground=MAU_CHON)
            o.grid(row=(m - 1) // so_cot, column=(m - 1) % so_cot, padx=4, pady=4, sticky="nsew")
            o.bind("<Button-1>", lambda e, so=m: self.chon_may(so))
        if self.may_chon is None:
            self.lbl_may_chon.config(text="Nhấn vào một máy để chọn.")
        else:
            self.lbl_may_chon.config(text=f"Máy đang chọn: {ten_may(self.may_chon)}")

    def dat_may_hong(self, hong):
        ma_ca = self.ma_ca()
        if not ma_ca:
            return
        if self.may_chon is None:
            messagebox.showinfo("Chưa chọn máy", "Vui lòng nhấn vào một máy trên sơ đồ trước.")
            return
        thanh_cong, noi_dung = self.ht.danh_dau_may_hong(ma_ca, self.may_chon, hong)
        self.thong_bao(thanh_cong, noi_dung)
        self.lam_moi_noi_dung()

    def xay_tab_danh_sach(self):
        khung = ttk.Frame(self.so_tab, padding=10)
        self.so_tab.add(khung, text="Danh sách sinh viên")

        hang = ttk.Frame(khung)
        hang.pack(fill="x", pady=(0, 8))
        ttk.Label(hang, text="Lọc:", font=FONT).pack(side="left", padx=(0, 6))
        cb = ttk.Combobox(hang, textvariable=self.var_loc, values=list(LOC_DANH_SACH.keys()),
                          state="readonly", width=26, font=FONT)
        cb.pack(side="left")
        cb.bind("<<ComboboxSelected>>", lambda e: self.lam_moi_danh_sach())
        ttk.Label(hang, text="Tìm (MSSV / họ tên):", font=FONT).pack(side="left", padx=(16, 6))
        o_tim = ttk.Entry(hang, textvariable=self.var_tim, width=24, font=FONT)
        o_tim.pack(side="left")
        self.var_tim.trace_add("write", lambda *a: self.lam_moi_danh_sach())
        self.lbl_so_luong = ttk.Label(hang, text="", font=FONT)
        self.lbl_so_luong.pack(side="left", padx=12)

        khung_bang, self.bang_ds = tao_bang(khung, [
            ("MSSV", 110), ("Họ tên", 220), ("Máy được cấp", 110), ("Trạng thái", 130), ("Ghi chú", 360),
        ])
        khung_bang.pack(fill="both", expand=True)

        hang2 = ttk.Frame(khung)
        hang2.pack(fill="x", pady=(8, 0))
        ttk.Button(hang2, text="Đổi máy (máy hỏng)", command=self.doi_may).pack(side="left", padx=4)
        ttk.Button(hang2, text="Gỡ phạm quy (xử lý khiếu nại)", command=self.go_pham_quy).pack(side="left", padx=4)
        ttk.Button(hang2, text="Xóa khỏi ca thi", command=self.xoa_khoi_ca).pack(side="left", padx=4)

    def lam_moi_danh_sach(self):
        ma_ca = self.ma_ca()
        if not ma_ca or ma_ca not in self.ht.ca_thi:
            dien_bang(self.bang_ds, [])
            self.lbl_so_luong.config(text="")
            return
        ds = self.ht.ds_dang_ky(ma_ca, self.var_loc.get(), self.var_tim.get())
        dien_bang(self.bang_ds, [
            (sv.mssv, sv.ho_ten, ten_may(d.may) if d.may else "-", d.trang_thai, d.ghi_chu)
            for sv, d in ds
        ], [sv.mssv for sv, _ in ds])
        self.lbl_so_luong.config(text=f"({len(ds)} sinh viên)")

    def chon_trong_bang(self, bang):
        chon = bang.selection()
        if not chon:
            messagebox.showinfo("Chưa chọn", "Vui lòng chọn một dòng trong bảng trước.")
            return None
        return chon[0]

    def doi_may(self):
        mssv = self.chon_trong_bang(self.bang_ds)
        if not mssv:
            return
        if not messagebox.askyesno("Đổi máy", f"Máy hiện tại của MSSV {mssv} sẽ bị đánh dấu hỏng và cấp máy mới ngẫu nhiên. Tiếp tục?"):
            return
        thanh_cong, noi_dung = self.ht.doi_may(mssv, self.ma_ca())
        self.thong_bao(thanh_cong, noi_dung, "Đổi máy")
        self.lam_moi_noi_dung()

    def go_pham_quy(self):
        mssv = self.chon_trong_bang(self.bang_ds)
        if not mssv:
            return
        kq = self.hop_thoai(f"Gỡ phạm quy – MSSV {mssv}", [("ly_do", "Lý do xử lý:", "", None)], "Xác nhận")
        if kq is None:
            return
        thanh_cong, noi_dung = self.ht.xu_ly_pham_quy(mssv, self.ma_ca(), kq["ly_do"])
        self.thong_bao(thanh_cong, noi_dung, "Xử lý phạm quy")
        self.lam_moi_noi_dung()

    def xoa_khoi_ca(self):
        mssv = self.chon_trong_bang(self.bang_ds)
        if not mssv:
            return
        if not messagebox.askyesno("Xóa khỏi ca thi", f"Xóa MSSV {mssv} khỏi ca {self.ma_ca()}?"):
            return
        thanh_cong, noi_dung = self.ht.xoa_dang_ky(mssv, self.ma_ca())
        self.thong_bao(thanh_cong, noi_dung)
        self.lam_moi_noi_dung()

    def xay_tab_ca_thi(self):
        khung = ttk.Frame(self.so_tab, padding=10)
        self.so_tab.add(khung, text="Quản lý ca thi")
        khung_bang, self.bang_ca = tao_bang(khung, [
            ("Mã ca", 70), ("Môn thi", 230), ("Ngày", 100), ("Giờ thi", 120),
            ("Phòng", 80), ("Số máy", 70), ("Số SV", 70), ("Trạng thái", 110),
        ], chieu_cao=14)
        khung_bang.pack(fill="both", expand=True)
        hang = ttk.Frame(khung)
        hang.pack(fill="x", pady=(8, 0))
        ttk.Button(hang, text="Thêm ca thi", command=self.them_ca).pack(side="left", padx=4)
        ttk.Button(hang, text="Sửa ca thi", command=self.sua_ca).pack(side="left", padx=4)
        ttk.Button(hang, text="Xóa ca thi", command=self.xoa_ca).pack(side="left", padx=4)

    def ve_tab_ca_thi(self):
        cac_ca = sorted(self.ht.ca_thi.values(), key=lambda c: (c.ngay, c.gio_bat_dau))
        dien_bang(self.bang_ca, [
            (c.ma_ca, c.mon_thi, hien_thi_ngay(c.ngay), f"{c.gio_bat_dau} – {c.gio_ket_thuc}", c.phong, c.so_may,
             sum(1 for d in self.ht.dang_ky if d.ma_ca == c.ma_ca), c.trang_thai())
            for c in cac_ca
        ], [c.ma_ca for c in cac_ca])

    def truong_ca(self, ca=None, co_ma=True):
        truong = []
        if co_ma:
            truong.append(("ma_ca", "Mã ca (ví dụ CA05):", "", None))
        truong += [
            ("mon_thi", "Môn thi:", ca.mon_thi if ca else "", None),
            ("ngay", "Ngày thi (YYYY-MM-DD):", ca.ngay if ca else date.today().strftime(DINH_DANG_NGAY), None),
            ("gio_bd", "Giờ bắt đầu (HH:MM):", ca.gio_bat_dau if ca else "07:30", None),
            ("gio_kt", "Giờ kết thúc (HH:MM):", ca.gio_ket_thuc if ca else "09:30", None),
            ("phong", "Phòng thi:", ca.phong if ca else "", None),
            ("so_may", "Số máy trong phòng:", ca.so_may if ca else "20", None),
        ]
        return truong

    def them_ca(self):
        kq = self.hop_thoai("Thêm ca thi", self.truong_ca())
        if kq is None:
            return
        thanh_cong, noi_dung = self.ht.them_ca(kq["ma_ca"], kq["mon_thi"], kq["ngay"],
                                              kq["gio_bd"], kq["gio_kt"], kq["phong"], kq["so_may"])
        self.thong_bao(thanh_cong, noi_dung, "Thêm ca thi")
        self.lam_moi()

    def sua_ca(self):
        ma_ca = self.chon_trong_bang(self.bang_ca)
        if not ma_ca:
            return
        kq = self.hop_thoai(f"Sửa ca thi {ma_ca}", self.truong_ca(self.ht.ca_thi[ma_ca], co_ma=False))
        if kq is None:
            return
        thanh_cong, noi_dung = self.ht.sua_ca(ma_ca, kq["mon_thi"], kq["ngay"],
                                             kq["gio_bd"], kq["gio_kt"], kq["phong"], kq["so_may"])
        self.thong_bao(thanh_cong, noi_dung, "Sửa ca thi")
        self.lam_moi()

    def xoa_ca(self):
        ma_ca = self.chon_trong_bang(self.bang_ca)
        if not ma_ca:
            return
        if not messagebox.askyesno("Xóa ca thi", f"Xóa ca {ma_ca} sẽ xóa luôn toàn bộ danh sách đăng ký và phân máy của ca. Tiếp tục?"):
            return
        thanh_cong, noi_dung = self.ht.xoa_ca(ma_ca)
        self.thong_bao(thanh_cong, noi_dung, "Xóa ca thi")
        self.lam_moi()

    def xay_tab_sinh_vien(self):
        khung = ttk.Frame(self.so_tab, padding=10)
        self.so_tab.add(khung, text="Quản lý sinh viên")

        hang = ttk.Frame(khung)
        hang.pack(fill="x", pady=(0, 8))
        ttk.Label(hang, text="Tìm (MSSV / họ tên):", font=FONT).pack(side="left", padx=(0, 6))
        ttk.Entry(hang, textvariable=self.var_tim_sv, width=26, font=FONT).pack(side="left")
        self.var_tim_sv.trace_add("write", lambda *a: self.ve_tab_sinh_vien())

        khung_bang, self.bang_sv = tao_bang(khung, [
            ("MSSV", 100), ("Họ tên", 200), ("Mã ca", 70), ("Môn thi", 210),
            ("Ngày", 100), ("Máy", 80), ("Trạng thái", 120),
        ], chieu_cao=12)
        khung_bang.pack(fill="both", expand=True)

        hang2 = ttk.Frame(khung)
        hang2.pack(fill="x", pady=(8, 0))
        ttk.Button(hang2, text="Thêm sinh viên vào ca", command=self.them_sinh_vien).pack(side="left", padx=4)
        ttk.Button(hang2, text="Xóa đăng ký đã chọn", command=self.xoa_dang_ky).pack(side="left", padx=4)
        ttk.Button(hang2, text="Import từ CSV (mssv, ho_ten, ma_ca)", command=self.import_csv).pack(side="left", padx=4)

    def ve_tab_sinh_vien(self):
        tu_khoa = self.var_tim_sv.get().strip().lower()
        hang, iid_ds = [], []
        for d in sorted(self.ht.dang_ky, key=lambda x: (x.mssv, x.ma_ca)):
            sv, ca = self.ht.sinh_vien.get(d.mssv), self.ht.ca_thi.get(d.ma_ca)
            if sv is None or ca is None:
                continue
            if tu_khoa and tu_khoa not in sv.mssv.lower() and tu_khoa not in sv.ho_ten.lower():
                continue
            hang.append((sv.mssv, sv.ho_ten, ca.ma_ca, ca.mon_thi, hien_thi_ngay(ca.ngay),
                         ten_may(d.may) if d.may else "-", d.trang_thai))
            iid_ds.append(f"{d.mssv}|{d.ma_ca}")
        dien_bang(self.bang_sv, hang, iid_ds)

    def them_sinh_vien(self):
        nhan_ds = list(self.nhan_ca.keys())
        if not nhan_ds:
            messagebox.showinfo("Chưa có ca thi", "Vui lòng tạo ca thi trước.")
            return
        kq = self.hop_thoai("Thêm sinh viên vào ca thi", [
            ("mssv", "MSSV:", "", None),
            ("ho_ten", "Họ tên (bỏ trống nếu MSSV đã có):", "", None),
            ("ca", "Ca thi:", self.cb_ca.get() or nhan_ds[0], nhan_ds),
        ])
        if kq is None:
            return
        thanh_cong, noi_dung = self.ht.them_sinh_vien_vao_ca(kq["mssv"], kq["ho_ten"], self.nhan_ca[kq["ca"]])
        self.thong_bao(thanh_cong, noi_dung, "Thêm sinh viên")
        self.lam_moi_noi_dung()

    def xoa_dang_ky(self):
        iid = self.chon_trong_bang(self.bang_sv)
        if not iid:
            return
        mssv, ma_ca = iid.split("|")
        if not messagebox.askyesno("Xóa đăng ký", f"Xóa MSSV {mssv} khỏi ca {ma_ca}?"):
            return
        thanh_cong, noi_dung = self.ht.xoa_dang_ky(mssv, ma_ca)
        self.thong_bao(thanh_cong, noi_dung)
        self.lam_moi_noi_dung()

    def import_csv(self):
        duong_dan = filedialog.askopenfilename(
            title="Chọn file CSV (cột: mssv, ho_ten, ma_ca)",
            filetypes=[("File CSV", "*.csv"), ("Tất cả", "*.*")])
        if not duong_dan:
            return
        thanh_cong, noi_dung = self.ht.import_csv(duong_dan)
        (messagebox.showinfo if thanh_cong else messagebox.showerror)("Import CSV", noi_dung)
        self.lam_moi_noi_dung()

    def xay_tab_lich_su(self):
        khung = ttk.Frame(self.so_tab, padding=10)
        self.so_tab.add(khung, text="Lịch sử & nhật ký")
        trong = ttk.Notebook(khung)
        trong.pack(fill="both", expand=True)

        cap = ttk.Frame(trong, padding=6)
        trong.add(cap, text="Lịch sử cấp máy (ca đang chọn)")
        kb1, self.bang_cap = tao_bang(cap, [
            ("Thời gian", 160), ("MSSV", 110), ("Họ tên", 200), ("Máy", 90), ("Loại", 320),
        ], chieu_cao=14)
        kb1.pack(fill="both", expand=True)

        xt = ttk.Frame(trong, padding=6)
        trong.add(xt, text="Lịch sử xác thực (ca đang chọn)")
        kb2, self.bang_xt = tao_bang(xt, [
            ("Thời gian", 160), ("MSSV", 110), ("Họ tên", 200),
            ("Máy được cấp", 120), ("Máy đăng nhập", 120), ("Kết quả", 120),
        ], chieu_cao=14)
        kb2.pack(fill="both", expand=True)

        nk = ttk.Frame(trong, padding=6)
        trong.add(nk, text="Nhật ký hoạt động của cán bộ")
        kb3, self.bang_nk = tao_bang(nk, [("Thời gian", 170), ("Nội dung", 700)], chieu_cao=14)
        kb3.pack(fill="both", expand=True)

    def ve_lich_su(self, ma_ca):
        dien_bang(self.bang_cap, [
            (b["thoi_gian"], b["mssv"], b["ho_ten"], ten_may(b["may"]), b["loai"])
            for b in reversed(self.ht.lich_su_cap_may) if b["ma_ca"] == ma_ca
        ])
        dien_bang(self.bang_xt, [
            (b["thoi_gian"], b["mssv"], b["ho_ten"], ten_may(b["may_duoc_cap"]),
             ten_may(b["may_dang_nhap"]), b["ket_qua"])
            for b in reversed(self.ht.lich_su_xac_thuc) if b["ma_ca"] == ma_ca
        ])

    def ve_nhat_ky(self):
        dien_bang(self.bang_nk, [(b["thoi_gian"], b["noi_dung"]) for b in reversed(self.ht.nhat_ky)])

    def xay_tab_bao_cao(self):
        khung = ttk.Frame(self.so_tab, padding=20)
        self.so_tab.add(khung, text="Báo cáo & hệ thống")
        ttk.Label(khung, text="BÁO CÁO VÀ QUẢN TRỊ HỆ THỐNG", font=FONT_TIEU_DE).pack(pady=(0, 14))
        cac_nut = [
            ("Xuất kết quả phân máy ca đang chọn (CSV)", self.xuat_phan_may),
            ("Xuất danh sách vi phạm ca đang chọn (CSV)", self.xuat_vi_pham),
            ("Xuất biên bản vi phạm ca đang chọn (TXT)", self.xuat_bien_ban),
            ("Đặt lại toàn bộ phân máy của ca đang chọn", self.dat_lai_phan_may),
            ("Sao lưu dữ liệu", self.sao_luu),
            ("Khôi phục dữ liệu từ file sao lưu", self.khoi_phuc),
            ("Đổi mật khẩu giáo viên", self.doi_mat_khau),
        ]
        for nhan, ham in cac_nut:
            ttk.Button(khung, text=nhan, command=ham, width=50).pack(pady=5, ipady=3)

    def can_ca(self):
        ma_ca = self.ma_ca()
        if not ma_ca:
            messagebox.showinfo("Chưa có ca thi", "Vui lòng chọn một ca thi ở phía trên.")
        return ma_ca

    def xuat_phan_may(self):
        ma_ca = self.can_ca()
        if not ma_ca:
            return
        duong_dan = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=f"phan_may_{ma_ca}.csv",
                                                 filetypes=[("File CSV", "*.csv")])
        if duong_dan:
            messagebox.showinfo("Xuất CSV", self.ht.export_phan_may_csv(duong_dan, ma_ca))

    def xuat_vi_pham(self):
        ma_ca = self.can_ca()
        if not ma_ca:
            return
        duong_dan = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=f"vi_pham_{ma_ca}.csv",
                                                 filetypes=[("File CSV", "*.csv")])
        if duong_dan:
            messagebox.showinfo("Xuất CSV", self.ht.export_vi_pham_csv(duong_dan, ma_ca))

    def xuat_bien_ban(self):
        ma_ca = self.can_ca()
        if not ma_ca:
            return
        duong_dan = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=f"bien_ban_{ma_ca}.txt",
                                                 filetypes=[("File văn bản", "*.txt")])
        if duong_dan:
            messagebox.showinfo("Xuất biên bản", self.ht.export_bien_ban_txt(duong_dan, ma_ca))

    def dat_lai_phan_may(self):
        ma_ca = self.can_ca()
        if not ma_ca:
            return
        if not messagebox.askyesno("Đặt lại phân máy", f"Toàn bộ máy đã cấp và trạng thái của ca {ma_ca} sẽ bị xóa. Tiếp tục?"):
            return
        thanh_cong, noi_dung = self.ht.dat_lai_phan_may(ma_ca)
        self.thong_bao(thanh_cong, noi_dung)
        self.lam_moi_noi_dung()

    def sao_luu(self):
        mac_dinh = f"sao_luu_{bay_gio().strftime('%Y%m%d_%H%M%S')}.json"
        duong_dan = filedialog.asksaveasfilename(defaultextension=".json", initialfile=mac_dinh,
                                                 filetypes=[("File JSON", "*.json")])
        if duong_dan:
            messagebox.showinfo("Sao lưu", self.ht.sao_luu(duong_dan))

    def khoi_phuc(self):
        duong_dan = filedialog.askopenfilename(title="Chọn file sao lưu", filetypes=[("File JSON", "*.json")])
        if not duong_dan:
            return
        if not messagebox.askyesno("Khôi phục", "Dữ liệu hiện tại sẽ bị thay bằng file sao lưu. Tiếp tục?"):
            return
        thanh_cong, noi_dung = self.ht.khoi_phuc(duong_dan)
        self.thong_bao(thanh_cong, noi_dung, "Khôi phục")
        self.lam_moi()

    def doi_mat_khau(self):
        kq = self.hop_thoai("Đổi mật khẩu giáo viên", [
            ("cu", "Mật khẩu hiện tại:", "", "*"),
            ("moi", "Mật khẩu mới:", "", "*"),
            ("nhap_lai", "Nhập lại mật khẩu mới:", "", "*"),
        ], "Đổi mật khẩu")
        if kq is None:
            return
        if not self.ht.kiem_tra_mat_khau(kq["cu"]):
            messagebox.showerror("Đổi mật khẩu", "Mật khẩu hiện tại không đúng.")
        elif len(kq["moi"]) < 4:
            messagebox.showwarning("Đổi mật khẩu", "Mật khẩu mới phải có ít nhất 4 ký tự.")
        elif kq["moi"] != kq["nhap_lai"]:
            messagebox.showwarning("Đổi mật khẩu", "Mật khẩu nhập lại không khớp.")
        else:
            self.ht.doi_mat_khau(kq["moi"])
            messagebox.showinfo("Đổi mật khẩu", "Đã đổi mật khẩu thành công.")
            self.lam_moi_noi_dung()

    def lam_moi(self):
        try:
            self.ht.tai()
        except (ValueError, OSError):
            return
        truoc = self.ma_ca()
        cac_ca = sorted(self.ht.ca_thi.values(), key=lambda c: (c.ngay, c.gio_bat_dau))
        self.nhan_ca = {
            f"{c.ma_ca} – {c.mon_thi} – {hien_thi_ngay(c.ngay)} {c.gio_bat_dau}-{c.gio_ket_thuc}": c.ma_ca
            for c in cac_ca
        }
        self.cb_ca["values"] = list(self.nhan_ca.keys())
        chon = next((nhan for nhan, ma in self.nhan_ca.items() if ma == truoc), None)
        if chon is None:
            chon = next((nhan for nhan, ma in self.nhan_ca.items() if self.ht.ca_thi[ma].la_hom_nay()), None)
        if chon is None and self.nhan_ca:
            chon = next(iter(self.nhan_ca))
        self.cb_ca.set(chon or "")
        self.lam_moi_noi_dung()

    def lam_moi_noi_dung(self):
        self.mtime_cu = lay_mtime(self.ht.file_du_lieu)
        self.ve_tab_ca_thi()
        self.ve_tab_sinh_vien()
        self.ve_nhat_ky()
        ma_ca = self.ma_ca()
        if not ma_ca or ma_ca not in self.ht.ca_thi:
            self.lbl_trang_thai_ca.config(text="Chưa có ca thi nào")
            for w in self.khung_may.winfo_children():
                w.destroy()
            for bang in (self.bang_ds, self.bang_cap, self.bang_xt):
                dien_bang(bang, [])
            for lbl in self.the_so.values():
                lbl.config(text="0")
            self.thanh_tien_do["value"] = 0
            self.lbl_ty_le.config(text="")
            return
        ca = self.ht.ca_thi[ma_ca]
        self.lbl_trang_thai_ca.config(text=f"Trạng thái ca: {ca.trang_thai()}  |  Phòng {ca.phong}")
        self.ve_tong_quan(ma_ca)
        self.ve_so_do(ma_ca)
        self.lam_moi_danh_sach()
        self.ve_lich_su(ma_ca)


class UngDung(tk.Tk):
    TIEU_DE = {
        "chinh": "HỆ THỐNG QUẢN LÝ CA THI",
        "sinh_vien": "GIAO DIỆN SINH VIÊN",
        "giao_vien": "GIAO DIỆN GIÁO VIÊN / CÁN BỘ COI THI",
    }

    def __init__(self, may_co_dinh=None):
        super().__init__()
        self.title("Hệ thống quản lý ca thi")
        self.geometry("1120x720")
        self.minsize(1000, 640)
        ttk.Style(self).configure("Lon.TButton", font=("Arial", 15), padding=14)

        self.ht = HeThongCaThi()
        self.ten_hien_tai = "chinh"

        thanh = ttk.Frame(self, padding=(10, 8))
        thanh.pack(fill="x")
        self.lbl_tieu_de = ttk.Label(thanh, font=("Arial", 14, "bold"))
        self.lbl_tieu_de.pack(side="left")
        self.nut_ve = ttk.Button(thanh, text="← Về màn hình chính", command=self.ve_man_hinh_chinh)
        self.lbl_dong_ho = ttk.Label(thanh, font=FONT)
        self.lbl_dong_ho.pack(side="right")
        ttk.Separator(self).pack(fill="x")

        khung = ttk.Frame(self)
        khung.pack(fill="both", expand=True)
        self.man_hinh = {
            "chinh": ManHinhChinh(khung, self),
            "sinh_vien": GiaoDienSinhVien(khung, self.ht, may_co_dinh),
            "giao_vien": GiaoDienGiaoVien(khung, self.ht),
        }
        self.hien("chinh")
        self.cap_nhat_dong_ho()
        self.after(2000, self.tu_dong_lam_moi)

    def hien(self, ten):
        for m in self.man_hinh.values():
            m.pack_forget()
        self.man_hinh[ten].pack(fill="both", expand=True)
        self.ten_hien_tai = ten
        self.lbl_tieu_de.config(text=self.TIEU_DE[ten])
        if ten == "chinh":
            self.nut_ve.pack_forget()
        else:
            self.nut_ve.pack(side="left", padx=(0, 14), before=self.lbl_tieu_de)

    def ve_man_hinh_chinh(self):
        self.hien("chinh")

    def vao_sinh_vien(self):
        self.man_hinh["sinh_vien"].dat_lai()
        self.hien("sinh_vien")

    def vao_giao_vien(self):
        kq = HopThoaiForm(self, "Đăng nhập giáo viên", [("mk", "Mật khẩu:", "", "*")], "Đăng nhập").ket_qua
        if kq is None:
            return
        if not self.ht.kiem_tra_mat_khau(kq["mk"]):
            messagebox.showerror("Đăng nhập", "Mật khẩu không đúng.")
            return
        self.man_hinh["giao_vien"].lam_moi()
        self.hien("giao_vien")

    def cap_nhat_dong_ho(self):
        self.lbl_dong_ho.config(text=bay_gio().strftime("Hôm nay: %d/%m/%Y   %H:%M:%S"))
        self.after(1000, self.cap_nhat_dong_ho)

    def tu_dong_lam_moi(self):
        if self.ten_hien_tai == "giao_vien":
            gv = self.man_hinh["giao_vien"]
            if lay_mtime(self.ht.file_du_lieu) != gv.mtime_cu:
                gv.lam_moi()
        self.after(2000, self.tu_dong_lam_moi)


def main() -> None:
    parser = argparse.ArgumentParser(description="Hệ thống quản lý ca thi")
    parser.add_argument("--may", type=int,
                        help="Cố định số máy của máy thi này cho tab Xác thực của sinh viên (ví dụ --may 12)")
    args = parser.parse_args()
    UngDung(may_co_dinh=args.may).mainloop()


if __name__ == "__main__":
    main()

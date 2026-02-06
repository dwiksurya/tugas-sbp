from tabulate import tabulate
from datetime import datetime

nasabah_list = []
auto_id_increment = 1

def tentukan_kelayakan(pendapatan, jumlah_pinjaman, pekerjaan_stabil, skor_slik, jaminan):
    rasio = jumlah_pinjaman / pendapatan if pendapatan > 0 else 0

    if skor_slik == 5:
        return "RESIKO", rasio, "SLIK macet"

    if rasio <= 3 and skor_slik <= 2 and pekerjaan_stabil:
        return "GOOD", rasio, "Risiko rendah"

    if rasio <= 5 and skor_slik <= 3 and (pekerjaan_stabil or jaminan):
        return "MODERATE", rasio, "Risiko sedang"

    return "RESIKO", rasio, "Risiko tinggi"


def tambah_nasabah():
    global auto_id_increment

    nama = input("Nama: ")
    pendapatan = float(input("Pendapatan: "))
    pinjaman = float(input("Jumlah Pinjaman: "))
    pekerjaan = input("Pekerjaan stabil? (y/n): ").lower() == "y"
    skor = int(input("Skor SLIK (1-5): "))
    jaminan = input("Ada jaminan? (y/n): ").lower() == "y"

    kelayakan, rasio, alasan = tentukan_kelayakan(
        pendapatan, pinjaman, pekerjaan, skor, jaminan
    )

    data = {
        "id": auto_id_increment,
        "nama": nama,
        "pendapatan": pendapatan,
        "pinjaman": pinjaman,
        "pekerjaan_stabil": pekerjaan,
        "skor_slik": skor,
        "jaminan": jaminan,
        "rasio": round(rasio, 2),
        "kelayakan": kelayakan,
        "alasan": alasan,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    nasabah_list.append(data)
    auto_id_increment += 1

    print("Data berhasil ditambahkan")


def lihat_nasabah():
    if not nasabah_list:
        print("Belum ada data")
        return

    table = []
    for n in nasabah_list:
        table.append([
            n["id"],
            n["nama"],
            n["pendapatan"],
            n["pinjaman"],
            "Ya" if n["pekerjaan_stabil"] else "Tidak",
            n["skor_slik"],
            "Ya" if n["jaminan"] else "Tidak",
            n["rasio"],
            n["kelayakan"],
            n["alasan"]
        ])

    headers = ["ID", "Nama", "Pendapatan", "Pinjaman", "Stabil", "SLIK", "Jaminan", "Rasio", "Status", "Alasan"]
    print(tabulate(table, headers=headers, tablefmt="grid"))


def edit_nasabah():
    idn = int(input("Masukkan ID: "))

    for n in nasabah_list:
        if n["id"] == idn:
            nama = input(f"Nama ({n['nama']}): ") or n["nama"]
            pendapatan = float(input(f"Pendapatan ({n['pendapatan']}): ") or n["pendapatan"])
            pinjaman = float(input(f"Pinjaman ({n['pinjaman']}): ") or n["pinjaman"])
            pekerjaan = input("Pekerjaan stabil? (y/n): ").lower() == "y"
            skor = int(input(f"Skor SLIK ({n['skor_slik']}): ") or n["skor_slik"])
            jaminan = input("Ada jaminan? (y/n): ").lower() == "y"

            kelayakan, rasio, alasan = tentukan_kelayakan(
                pendapatan, pinjaman, pekerjaan, skor, jaminan
            )

            n.update({
                "nama": nama,
                "pendapatan": pendapatan,
                "pinjaman": pinjaman,
                "pekerjaan_stabil": pekerjaan,
                "skor_slik": skor,
                "jaminan": jaminan,
                "rasio": round(rasio, 2),
                "kelayakan": kelayakan,
                "alasan": alasan
            })

            print("Data berhasil diupdate")
            return

    print("ID tidak ditemukan")


def hapus_nasabah():
    idn = int(input("Masukkan ID yang akan dihapus: "))

    for i, n in enumerate(nasabah_list):
        if n["id"] == idn:
            nasabah_list.pop(i)
            print("🗑 Data berhasil dihapus")
            return

    print("ID tidak ditemukan")


def menu():
    print("\n===== CEK KELAYAKAN KREDIT NASABAH =====")
    print("1. Tambah Nasabah")
    print("2. Lihat Nasabah")
    print("3. Edit Nasabah")
    print("4. Hapus Nasabah")
    print("0. Keluar")


def main():
    while True:
        menu()
        pilih = input("Pilih menu: ")

        if pilih == "1":
            tambah_nasabah()
        elif pilih == "2":
            lihat_nasabah()
        elif pilih == "3":
            edit_nasabah()
        elif pilih == "4":
            hapus_nasabah()
        elif pilih == "0":
            print("Program ditutup")
            break
        else:
            print("Menu tidak valid")


if __name__ == "__main__":
    main()

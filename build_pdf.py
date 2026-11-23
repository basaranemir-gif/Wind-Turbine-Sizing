"""
WindTurbineSizing_Rapor.pdf oluşturur. make_report.py'den kaydedilen
_results.npz ile aero verisini kullanıp grafikli, Türkçe, yalın bir rapor üretir.
"""
import os
os.environ.setdefault('MPLCONFIGDIR', '/tmp/mplcache')
os.makedirs('/tmp/mplcache', exist_ok=True)

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

import make_report as M   # reuse loaded aero + control curves + results

plt.rcParams.update({'font.family': 'DejaVu Sans', 'axes.grid': True,
                     'grid.alpha': 0.3})

R = np.load('_results.npz', allow_pickle=True)
CLASSES, VAVE, COLORS = M.CLASSES, M.VAVE, M.COLORS
aero2, cc0, res0 = M.aero2, M.cc0, M.res0
tsr_opt = float(R['tsr_opt']); pitch_opt = float(R['pitch_opt'])
cp_max = float(R['cp_max']); cq_r2 = float(R['cq_r2'])
V_lim = float(R['V_lim']); Omega_max = float(R['Omega_max'])

A4 = (8.27, 11.69)
BLUE = '#1f6f8b'


def page_title(fig, title, sub=None):
    fig.text(0.5, 0.965, title, ha='center', va='top', fontsize=17,
             fontweight='bold', color=BLUE)
    if sub:
        fig.text(0.5, 0.935, sub, ha='center', va='top', fontsize=10.5,
                 color='#555')
    fig.add_artist(plt.Line2D([0.08, 0.92], [0.925, 0.925], color=BLUE,
                              lw=1.2, transform=fig.transFigure))


def wrap_text(fig, x, y, text, fontsize=10, color='black', weight='normal'):
    fig.text(x, y, text, ha='left', va='top', fontsize=fontsize, color=color,
             fontweight=weight, wrap=True)


with PdfPages('WindTurbineSizing_Rapor.pdf') as pdf:

    # ---------- KAPAK ----------
    fig = plt.figure(figsize=A4)
    fig.add_artist(plt.Line2D([0.1, 0.9], [0.74, 0.74], color=BLUE, lw=2,
                              transform=fig.transFigure))
    fig.text(0.5, 0.80, 'Rüzgar Türbini Boyutlandırma', ha='center',
             fontsize=28, fontweight='bold', color=BLUE)
    fig.text(0.5, 0.755, 'Kontrol Eğrileri, AEP ve Enerji Maliyeti (CoE) Analizi',
             ha='center', fontsize=13, color='#555')
    fig.text(0.5, 0.70, 'TUM Wind Energy Institute — Ödev Çözümü',
             ha='center', fontsize=11, color='#777')
    intro = (
        "Bu rapor, bir rüzgar türbininin aerodinamik performansından yola çıkarak\n"
        "kontrol eğrilerini türetir; ardından rotor çapı ve kule yüksekliğini,\n"
        "enerji maliyetini (CoE) en aza indirecek şekilde boyutlandırır.\n\n"
        "Tüm sayılar, ödevin MATLAB kodundaki aynı mantık (comp_ControlCurves,\n"
        "comp_AEPandCOE, CostModel) Python'da çalıştırılarak üretilmiştir.\n\n"
        "Temel türbin (2 MW):\n"
        "   • Nominal güç Pr = 2 MW\n"
        "   • Rotor çapı D = 92.4 m\n"
        "   • Göbek yüksekliği H = 90 m\n"
        "   • Verim η = 0.9\n"
        "   • Maks. kanat ucu hızı Vtip,max = 72 m/s"
    )
    fig.text(0.14, 0.60, intro, ha='left', va='top', fontsize=11.5,
             color='#333', linespacing=1.6)
    # small Cp surface thumbnail
    ax = fig.add_axes([0.30, 0.09, 0.42, 0.26], projection='3d')
    T, P = aero2['tsr'], aero2['pitch']
    TT, PP = np.meshgrid(T, P, indexing='ij')
    ax.plot_surface(TT, PP, np.nan_to_num(aero2['Cp']), cmap='viridis',
                    linewidth=0, antialiased=True, alpha=0.9)
    ax.set_xlabel('TSR', fontsize=7); ax.set_ylabel('Pitch [°]', fontsize=7)
    ax.set_zlabel('Cp', fontsize=7)
    ax.tick_params(labelsize=6)
    ax.set_title('Cp(λ, β) yüzeyi', fontsize=9)
    pdf.savefig(fig); plt.close(fig)

    # ---------- SAYFA 1: Aerodinamik performans (Task 2) ----------
    fig = plt.figure(figsize=A4)
    page_title(fig, 'Görev 2 — Aerodinamik Performans (Cp, Cq)',
               'Türbin en verimli noktasında (maksimum Cp) çalışmak ister. Bu nokta Region 2 işletme noktasıdır.')
    # Cp vs TSR
    ax1 = fig.add_axes([0.1, 0.60, 0.37, 0.26])
    for col in range(0, aero2['Cp'].shape[1], 3):
        ax1.plot(aero2['tsr'], aero2['Cp'][:, col], lw=0.8, alpha=0.6)
    ax1.scatter([tsr_opt], [cp_max], color='red', zorder=5, s=40,
                label=f'Maks Cp={cp_max:.3f}')
    ax1.set_xlabel('λ (TSR)'); ax1.set_ylabel('Cp'); ax1.set_ylim(0, 0.6)
    ax1.set_title('Cp — λ eğrileri (farklı pitch)', fontsize=10)
    ax1.legend(fontsize=8)
    # Cq vs TSR
    ax2 = fig.add_axes([0.57, 0.60, 0.37, 0.26])
    for col in range(0, aero2['Cq'].shape[1], 3):
        ax2.plot(aero2['tsr'], aero2['Cq'][:, col], lw=0.8, alpha=0.6)
    ax2.scatter([tsr_opt], [cq_r2], color='red', zorder=5, s=40)
    ax2.set_xlabel('λ (TSR)'); ax2.set_ylabel('Cq'); ax2.set_ylim(0, 0.1)
    ax2.set_title('Cq — λ eğrileri', fontsize=10)
    # table
    rows = [['Cp (Region 2)', f'{cp_max:.4f}'],
            ['Cq (Region 2)', f'{cq_r2:.5f}  (= Cp/λ)'],
            ['λ (Region 2)', f'{tsr_opt:.2f}'],
            ['β (Region 2)', f'{pitch_opt:.2f}°']]
    axt = fig.add_axes([0.2, 0.34, 0.6, 0.16]); axt.axis('off')
    tbl = axt.table(cellText=rows, colLabels=['Büyüklük', 'Region 2 değeri'],
                    cellLoc='center', loc='center')
    tbl.auto_set_font_size(False); tbl.set_fontsize(11); tbl.scale(1, 1.8)
    for (r, c), cell in tbl.get_celld().items():
        if r == 0:
            cell.set_facecolor(BLUE); cell.set_text_props(color='white', weight='bold')
    txt = (
        "Yalın açıklama:\n"
        "• Cp = güç katsayısı → rüzgardaki enerjinin ne kadarını türbin yakalıyor (teorik üst sınır Betz: 0.593).\n"
        "• Bizim türbinimiz en iyi ~0.484 yakalıyor; λ≈7.65 ve pitch≈−0.8° ayarında.\n"
        "• Region 2'de bu TEK nokta sabit tutulur: pitch ve λ değişmez, sadece rotor hızı rüzgarla artar.\n"
        "• Cq (tork katsayısı) = Cp / λ. Bu yüzden Cq eğrisinin tepesi, Cp tepesiyle aynı noktada değildir."
    )
    wrap_text(fig, 0.1, 0.28, txt, fontsize=10.5, color='#333')
    pdf.savefig(fig); plt.close(fig)

    # ---------- SAYFA 2: Vtip ve Kontrol Bölgeleri (Task 3+4+5) ----------
    fig = plt.figure(figsize=A4)
    page_title(fig, 'Görev 3–5 — Kanat Ucu Hızı ve Kontrol Bölgeleri',
               'Türbin, rüzgar hızına göre dört farklı "bölge"de farklı strateji uygular.')
    cc = cc0; V = cc['winds']
    i_end, j_end = cc['idx']
    V2, V25 = V[i_end], V[j_end]
    # shaded control trajectory: power + rpm
    ax1 = fig.add_axes([0.1, 0.58, 0.84, 0.28])
    ax1.plot(V, cc['Power']/1e6, color='#c0392b', lw=2.2, label='Güç [MW]')
    ax1b = ax1.twinx()
    ax1b.plot(V, cc['Omega']*30/np.pi, color='#2980b9', lw=2.0, ls='--',
              label='Rotor hızı [rpm]')
    ax1.axvspan(V[0], V2, color='#2ecc71', alpha=0.08)
    ax1.axvspan(V2, V25, color='#f1c40f', alpha=0.12)
    ax1.axvspan(V25, V[-1], color='#e67e22', alpha=0.10)
    for xv, lab in [((V[0]+V2)/2, 'Region 2'), ((V2+V25)/2, 'R 2½'),
                    ((V25+V[-1])/2, 'Region 3')]:
        ax1.text(xv, 0.2, lab, ha='center', fontsize=9, color='#444')
    ax1.set_xlabel('Rüzgar hızı V∞ [m/s]'); ax1.set_ylabel('Güç [MW]', color='#c0392b')
    ax1b.set_ylabel('Rotor hızı [rpm]', color='#2980b9')
    ax1.set_title('Kontrol trajesi: güç ve rotor hızı', fontsize=10)
    l1, lab1 = ax1.get_legend_handles_labels()
    l2, lab2 = ax1b.get_legend_handles_labels()
    ax1.legend(l1+l2, lab1+lab2, fontsize=8, loc='center right')
    # pitch + TSR
    ax2 = fig.add_axes([0.1, 0.30, 0.37, 0.20])
    ax2.plot(V, cc['Pitch'], color='#8e44ad', lw=2)
    ax2.axvline(V2, color='gray', ls=':'); ax2.axvline(V25, color='gray', ls=':')
    ax2.set_xlabel('V∞ [m/s]'); ax2.set_ylabel('Pitch β [°]')
    ax2.set_title('Pitch açısı', fontsize=9)
    ax3 = fig.add_axes([0.57, 0.30, 0.37, 0.20])
    ax3.plot(V, cc['TSR'], color='#16a085', lw=2)
    ax3.axvline(V2, color='gray', ls=':'); ax3.axvline(V25, color='gray', ls=':')
    ax3.set_xlabel('V∞ [m/s]'); ax3.set_ylabel('λ (TSR)')
    ax3.set_title('Tip-speed ratio', fontsize=9)
    txt = (
        f"Görev 3 — Kanat ucu sınırına ulaşılan hız:\n"
        f"   V∞(Vtip,max) = Vtip,max / λ = 72 / {tsr_opt:.2f} = {V_lim:.2f} m/s\n"
        f"   Ω_max = Vtip,max / R = 72 / 46.2 = {Omega_max:.3f} rad/s = {Omega_max*30/np.pi:.2f} rpm\n\n"
        "Görev 4 — Bölgelerin kontrol tanımı:\n"
        "   Region 1  : V < 3 m/s. Rüzgar yetersiz, türbin güç üretmez.\n"
        "   Region 2  : Maks. verim. λ ve β sabit, Cp=Cp_max. Rotor hızı rüzgarla artar.\n"
        "   Region 2½ : Vtip,max'a ulaşıldı → rotor hızı sabit. λ düşer, pitch yeniden\n"
        "               optimize edilir. Henüz nominal güce ulaşılmadı.\n"
        "   Region 3  : V > V_rated. Güç nominal değerde sabit; fazla güç pitch ile atılır.\n\n"
        f"Neden Region 2½ var?  Kanat ucu hızı sınırına ({V_lim:.1f} m/s), nominal güce\n"
        f"ulaşmadan ÖNCE varılıyor. Araya bir geçiş bölgesi giriyor ({V2:.1f}→{V25:.1f} m/s).\n\n"
        "Görev 5 — Küçük çapta Region 2½ neden büyür?  Sınırın başladığı hız (Vtip/λ)\n"
        "çaptan bağımsızdır; ama küçük rotor daha az güç yakaladığından nominal güce\n"
        "daha yüksek rüzgarda ulaşır → bölgenin sonu sağa kayar, Region 2½ genişler."
    )
    wrap_text(fig, 0.08, 0.25, txt, fontsize=9.3, color='#333')
    pdf.savefig(fig); plt.close(fig)

    # ---------- SAYFA 3: AEP, CoE, Kapasite Faktörü (Task 6) ----------
    fig = plt.figure(figsize=A4)
    page_title(fig, 'Görev 6 — Yıllık Enerji (AEP), Maliyet (CoE), Kapasite Faktörü',
               'Her IEC rüzgar sınıfı farklı ortalama rüzgar hızına sahiptir (Rayleigh dağılımı, k=2).')
    # weibull pdfs
    ax1 = fig.add_axes([0.1, 0.60, 0.37, 0.26])
    for r, col, cls in zip(res0, COLORS, CLASSES):
        ax1.plot(cc0['winds'], r['pdf'], color=col, lw=1.8,
                 label=f'Sınıf {cls} ({r["Vave"]} m/s)')
    ax1.set_xlabel('Rüzgar hızı [m/s]'); ax1.set_ylabel('Olasılık yoğunluğu')
    ax1.set_title('Rüzgar dağılımları', fontsize=10); ax1.legend(fontsize=7.5)
    # AEP bars
    ax2 = fig.add_axes([0.57, 0.60, 0.37, 0.26])
    ax2.bar(CLASSES, [r['AEP']/1e6 for r in res0], color=COLORS)
    ax2.set_ylabel('AEP [MWh/yıl]'); ax2.set_title('Yıllık enerji üretimi', fontsize=10)
    # CoE bars
    ax3 = fig.add_axes([0.1, 0.30, 0.37, 0.22])
    ax3.bar(CLASSES, [r['coe'] for r in res0], color=COLORS)
    ax3.set_ylabel('CoE [$/kWh]'); ax3.set_title('Enerji maliyeti', fontsize=10)
    # CF bars
    ax4 = fig.add_axes([0.57, 0.30, 0.37, 0.22])
    ax4.bar(CLASSES, [r['CF']*100 for r in res0], color=COLORS)
    ax4.set_ylabel('Kapasite faktörü [%]'); ax4.set_title('Kapasite faktörü', fontsize=10)
    # table
    rows = [[f'Sınıf {c}', f'{r["Vave"]}', f'{r["AEP"]/1e6:,.0f}',
             f'{r["coe"]:.4f}', f'{r["CF"]*100:.1f}%']
            for c, r in zip(CLASSES, res0)]
    axt = fig.add_axes([0.12, 0.09, 0.76, 0.16]); axt.axis('off')
    tbl = axt.table(cellText=rows,
                    colLabels=['Sınıf', 'V_avg [m/s]', 'AEP [MWh]', 'CoE [$/kWh]', 'Kap. Faktörü'],
                    cellLoc='center', loc='center')
    tbl.auto_set_font_size(False); tbl.set_fontsize(10); tbl.scale(1, 1.7)
    for (r, c), cell in tbl.get_celld().items():
        if r == 0:
            cell.set_facecolor(BLUE); cell.set_text_props(color='white', weight='bold')
    fig.text(0.12, 0.055, 'Yorum: Rüzgarlı sınıfta (I) AEP yüksek, CoE düşük. Sınıf IV\'te '
             'aynı türbin az üretir, CoE neredeyse iki katına çıkar.',
             fontsize=9.5, color='#333')
    pdf.savefig(fig); plt.close(fig)

    # ---------- SAYFA 4: Optimizasyon (Task 7+8+9) ----------
    fig = plt.figure(figsize=A4)
    page_title(fig, 'Görev 7–9 — Rotor Çapı ve Kule Yüksekliği Optimizasyonu',
               'CoE\'yi minimize eden boyutlar her rüzgar sınıfı için farklıdır.')
    Diam, coe_D, Dopt = R['Diam'], R['coe_D'], R['Dopt']
    Hub, coe_H, Hopt = R['Hub'], R['coe_H'], R['Hopt']
    combo = R['combo']
    ax1 = fig.add_axes([0.1, 0.60, 0.37, 0.26])
    for ci, (col, cls) in enumerate(zip(COLORS, CLASSES)):
        ax1.plot(Diam, coe_D[:, ci], color=col, lw=1.8, label=f'Sınıf {cls}')
        imin = np.argmin(coe_D[:, ci])
        ax1.scatter(Diam[imin], coe_D[imin, ci], color=col, marker='x', s=60)
    ax1.set_xlabel('Rotor çapı [m]'); ax1.set_ylabel('CoE [$/kWh]')
    ax1.set_title('Görev 7: çap taraması', fontsize=10); ax1.legend(fontsize=8)
    ax2 = fig.add_axes([0.57, 0.60, 0.37, 0.26])
    for ci, (col, cls) in enumerate(zip(COLORS, CLASSES)):
        ax2.plot(Hub, coe_H[:, ci], color=col, lw=1.8, label=f'Sınıf {cls}')
        imin = np.argmin(coe_H[:, ci])
        ax2.scatter(Hub[imin], coe_H[imin, ci], color=col, marker='x', s=60)
    ax2.set_xlabel('Kule yüksekliği [m]'); ax2.set_ylabel('CoE [$/kWh]')
    ax2.set_title('Görev 8: yükseklik taraması', fontsize=10); ax2.legend(fontsize=8)
    # combined heatmap for class II
    ax3 = fig.add_axes([0.18, 0.33, 0.64, 0.20])
    rows = [[f'Sınıf {c}', f'{R["Dopt"][i]:.1f}', f'{R["Hopt"][i]:.0f}',
             f'{combo[i][0]:.1f}', f'{combo[i][1]:.0f}', f'{combo[i][2]:.4f}']
            for i, c in enumerate(CLASSES)]
    ax3.axis('off')
    tbl = ax3.table(cellText=rows,
                    colLabels=['Sınıf', 'D_opt [m]', 'H_opt [m]', 'D_komb [m]', 'H_komb [m]', 'CoE_min'],
                    cellLoc='center', loc='center',
                    colWidths=[0.14, 0.17, 0.17, 0.18, 0.18, 0.16])
    tbl.auto_set_font_size(False); tbl.set_fontsize(8.5); tbl.scale(1, 1.7)
    for (r, c), cell in tbl.get_celld().items():
        if r == 0:
            cell.set_facecolor(BLUE); cell.set_text_props(color='white', weight='bold')
    txt = (
        "* Dopt: yalnız çap değişirken (H=90 m sabit). Hopt: yalnız yükseklik değişirken (D=92.4 m sabit).\n"
        "  D_kombi/H_kombi: ikisi birlikte tarandığında bulunan ortak optimum (Görev 9).\n\n"
        "Yalın açıklama:\n"
        "• Az rüzgarlı sınıflarda (III, IV) daha BÜYÜK rotor ve daha YÜKSEK kule tercih edilir:\n"
        "  rüzgar zayıf olduğunda daha fazla alan süpürmek ve yüksekteki daha hızlı rüzgara\n"
        "  ulaşmak kWh başına maliyeti düşürür.\n"
        "• Rüzgarlı sınıfta (I) ise türbin zaten çok üretir; büyütmek maliyeti artırır, o yüzden\n"
        "  optimum çap/yükseklik daha küçük kalır.\n"
        "• Görev 9: Çap ve yükseklik AYNI anda tarandığında bulunan ortak optimum, tek tek\n"
        "  optimize etmekten biraz farklıdır çünkü ikisi birbirini etkiler (rotor büyürse kule\n"
        "  maliyeti de artar)."
    )
    wrap_text(fig, 0.08, 0.27, txt, fontsize=9.3, color='#333')
    pdf.savefig(fig); plt.close(fig)

    # ---------- SAYFA 5: 10 MW Offshore (Task 10) ----------
    fig = plt.figure(figsize=A4)
    page_title(fig, 'Görev 10 — 10 MW Offshore Türbin (Yeni Nesil)',
               'Aynı analiz, D=178 m, H=119 m, Vtip,max=90 m/s, Pr=10 MW türbin için tekrarlandı.')
    res10 = M.res10; cc10 = M.cc10
    Diam10, coe_D10, Dopt10 = R['Diam10'], R['coe_D10'], R['Dopt10']
    t10, p10, cp10, cq10 = float(R['t10']), float(R['p10']), float(R['cp10']), float(R['cq10'])
    ax1 = fig.add_axes([0.1, 0.60, 0.37, 0.26])
    ax1.plot(cc10['winds'], cc10['Power']/1e6, color='#c0392b', lw=2.2)
    ax1.set_xlabel('V∞ [m/s]'); ax1.set_ylabel('Güç [MW]')
    ax1.set_title('10 MW güç eğrisi', fontsize=10)
    ax2 = fig.add_axes([0.57, 0.60, 0.37, 0.26])
    for ci, (col, cls) in enumerate(zip(COLORS, CLASSES)):
        ax2.plot(Diam10, coe_D10[:, ci], color=col, lw=1.8, label=f'Sınıf {cls}')
        imin = np.argmin(coe_D10[:, ci])
        ax2.scatter(Diam10[imin], coe_D10[imin, ci], color=col, marker='x', s=60)
    ax2.set_xlabel('Rotor çapı [m]'); ax2.set_ylabel('CoE [$/kWh]')
    ax2.set_title('Görev 10: çap taraması (10 MW)', fontsize=10); ax2.legend(fontsize=8)
    rows = [[f'Sınıf {c}', f'{r["AEP"]/1e6:,.0f}', f'{r["coe"]:.4f}',
             f'{r["CF"]*100:.1f}%', f'{Dopt10[i]:.0f}']
            for i, (c, r) in enumerate(zip(CLASSES, res10))]
    axt = fig.add_axes([0.12, 0.33, 0.76, 0.18]); axt.axis('off')
    tbl = axt.table(cellText=rows,
                    colLabels=['Sınıf', 'AEP [MWh]', 'CoE [$/kWh]', 'Kap.F.', 'Dopt [m]'],
                    cellLoc='center', loc='center')
    tbl.auto_set_font_size(False); tbl.set_fontsize(10); tbl.scale(1, 1.7)
    for (r, c), cell in tbl.get_celld().items():
        if r == 0:
            cell.set_facecolor(BLUE); cell.set_text_props(color='white', weight='bold')
    txt = (
        f"10 MW Region 2 noktası: Cp={cp10:.3f}, Cq={cq10:.4f}, λ={t10:.2f}, β={p10:.2f}°\n\n"
        "Yalın açıklama:\n"
        "• Büyük offshore türbin aynı rüzgardan çok daha fazla enerji üretir (AEP ~5 kat).\n"
        "• CoE, 2 MW türbine kıyasla daha düşük olabilir: büyük makineler ölçek ekonomisinden\n"
        "  yararlanır (kWh başına maliyet düşer).\n"
        "• Offshore'da rüzgar genelde daha güçlü ve düzenli olduğu için kapasite faktörü yüksektir.\n"
        "• Optimum çap, 2 MW türbine göre çok daha büyük (~215+ m) çıkar; özellikle düşük\n"
        "  rüzgar sınıflarında rotoru büyütmek hâlâ maliyeti düşürür."
    )
    wrap_text(fig, 0.08, 0.27, txt, fontsize=9.6, color='#333')
    fig.text(0.5, 0.05, 'Rüzgar Türbini Boyutlandırma — Analiz Raporu',
             ha='center', fontsize=8, color='#999')
    pdf.savefig(fig); plt.close(fig)

print('PDF yazildi: WindTurbineSizing_Rapor.pdf')

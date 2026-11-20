import discord
from discord.ext import commands, tasks
import os, json, time, asyncio, aiohttp, random
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "mipi_data.json"
VOUCH_CHANNEL_ID = 1571783490297528420
ORDER_LOGS_CHANNEL_ID = 1571783908058730547
TESTIMONI_CHANNEL_ID = 1571784387438055515
PROMO_CHANNEL_ID = 0
QRIS_URL = "https://raw.githubusercontent.com/mipistore/mipi-store/main/IMG_5210.jpeg"
DEMO_SERVER_INVITE = "https://discord.gg/5G3kJHPHb"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                d = json.load(f)
                d.setdefault("order_count", 0); d.setdefault("reviews", []); d.setdefault("orders", [])
                d.setdefault("promo_codes", {"MIPI10": {"diskon": 10, "dipakai": 0, "max": 50}})
                d.setdefault("affiliate", {}); d.setdefault("stok", {"simple": 99, "medium": 99, "full": 99, "premium": 10, "sultan": 5, "god": 2, "music": 99})
                d.setdefault("total_omset", 0)
                return d
        except: pass
    return {"order_count": 0, "reviews": [], "orders": [], "promo_codes": {"MIPI10": {"diskon": 10, "dipakai": 0, "max": 50}}, "affiliate": {}, "stok": {"simple": 99, "medium": 99, "full": 99, "premium": 10, "sultan": 5, "god": 2, "music": 99}, "total_omset": 0}

def save_data(d):
    try:
        with open(DATA_FILE, "w") as f: json.dump(d, f, indent=2)
    except: pass

DATA = load_data()
PENDING = {}; COOLDOWN = {}; MID_PENDING = {}

@bot.event
async def on_ready():
    print(f"Bot Online: {bot.user} | Omset: Rp {DATA.get('total_omset',0):,}")
    try: await bot.tree.sync()
    except Exception as e: print(e)
    if not auto_promo.is_running(): auto_promo.start()

CATEGORIES = {
    "bot": {"kategori": "Jasa Buat Bot", "rate": "Mulai Rp 25.000",
        "list": "• SIMPLE\n  └ 🏷️ Rp 25.000\n• MEDIUM\n  └ 🏷️ Rp 50.000\n• FULL\n  └ 🏷️ Rp 100.000\n• PREMIUM\n  └ 🏷️ Rp 150.000\n• SULTAN\n  └ 🏷️ Rp 250.000\n• GOD\n  └ 🏷️ Rp 500.000\n• BOT MUSIC\n  └ 🏷️ Rp 30.000",
        "products": [("💎 SIMPLE - Rp 25.000", "simple"), ("🛡️ MEDIUM - Rp 50.000", "medium"), ("⭐ FULL - Rp 100.000", "full"), ("👑 PREMIUM - Rp 150.000", "premium"), ("🔥 SULTAN - Rp 250.000", "sultan"), ("🧊 GOD - Rp 500.000", "god"), ("🎵 BOT MUSIC - Rp 30.000", "music")]},
    "setup": {"kategori": "Jasa Setup DC", "rate": "Mulai Rp 25.000",
        "list": "• SETUP SIMPLE\n  └ 🏷️ Rp 25.000\n• SETUP MEDIUM\n  └ 🏷️ Rp 50.000\n• SETUP FULL\n  └ 🏷️ Rp 100.000\n• SETUP PREMIUM\n  └ 🏷️ Rp 150.000\n• SETUP SULTAN\n  └ 🏷️ Rp 250.000",
        "products": [("🛠️ SETUP SIMPLE - Rp 25.000", "setup_simple"), ("🛠️ SETUP MEDIUM - Rp 50.000", "setup_medium"), ("🛠️ SETUP FULL - Rp 100.000", "setup_full"), ("🛠️ SETUP PREMIUM - Rp 150.000", "setup_premium"), ("🛠️ SETUP SULTAN - Rp 250.000", "setup_sultan")]},
}
PRODUCTS_DETAIL = {
    "simple": ("💎 SIMPLE", 25000, "Ticket + QRIS + Status + Close"),
    "medium": ("🛡️ MEDIUM", 50000, "Simple + Saldo + Leaderboard + Vouch + Giveaway"),
    "full": ("⭐ FULL", 100000, "Medium + Promo + Anti Jualan + History + 7 Produk + Custom + Diajarin Sampai Bisa"),
    "premium": ("👑 PREMIUM", 150000, "Semua Full + 7 Fitur Custom + Setup Hosting + Support Lifetime"),
    "sultan": ("🔥 SULTAN", 250000, "Semua Premium + 5 Fitur Custom + 2 Bot + Banner Gratis + VIP"),
    "god": ("🧊 GOD", 500000, "Semua Sultan + Unlimited + Source Code + Partner MIPI"),
    "music": ("🎵 BOT MUSIC", 30000, "Music 24/7 + Play / Skip / Queue + Spotify & Youtube"),
    "setup_simple": ("🛠️ SETUP SIMPLE", 25000, "Channel + Role + Kategori + Rules"),
    "setup_medium": ("🛠️ SETUP MEDIUM", 50000, "Simple + Ticket + Welcome + Vouch + Pricelist"),
    "setup_full": ("🛠️ SETUP FULL", 100000, "Medium + Bot Ticket + Leaderboard + Banner + Catalog"),
    "setup_premium": ("🛠️ SETUP PREMIUM", 150000, "Semua Full + Custom Design + Setup Hosting + Support 7 Hari"),
    "setup_sultan": ("🛠️ SETUP SULTAN", 250000, "Semua Premium + 2 Bot + Banner Gratis + VIP + Support Lifetime"),
}
def fmt_rp(n): return f"Rp {n:,}".replace(",", ".")

def find_channel(guild, name_part):
    for cid in [VOUCH_CHANNEL_ID, ORDER_LOGS_CHANNEL_ID, TESTIMONI_CHANNEL_ID]:
        ch = guild.get_channel(cid)
        if ch and name_part in ch.name.lower(): return ch
    for ch in guild.text_channels:
        if name_part in ch.name.lower(): return ch
    return None

def get_vouch_embed(r):
    e = discord.Embed(title="⭐ TESTIMONI PEMBELI — Mipi Store", color=0xFFD700)
    e.add_field(name="👤 Pembeli:", value=r["customer_mention"], inline=False)
    e.add_field(name="📦 Produk:", value=r["produk"], inline=False)
    e.add_field(name="⭐ Rating:", value=f"{'⭐'*r['rating']} ({r['rating']}/5)", inline=False)
    e.add_field(name="💬 Ulasan:", value=f"\"{r['ulasan']}\"", inline=False)
    e.add_field(name="📅 Tanggal:", value=r["tanggal"], inline=False)
    if r.get("avatar"): e.set_thumbnail(url=r["avatar"])
    return e

def get_order_log_embed(o):
    e = discord.Embed(title=f"🧾 ORDER LOG — {o['order_id']}", color=0x2B2D31)
    for k,v in [("👤 Customer:", o["customer_mention"]), ("📦 Produk:", o["produk"]), ("💰 Total Bayar:", o["harga"]), ("💳 Metode:", "QRIS"), ("📅 Tanggal:", o["tanggal"]), ("📊 Status:", "🟢 DONE / PAID")]: e.add_field(name=k, value=v, inline=False)
    if o.get("avatar"): e.set_thumbnail(url=o["avatar"])
    return e

async def update_testimoni(guild):
    ch = find_channel(guild, "testimoni")
    if not ch: return
    reviews = DATA.get("reviews", []); total = len(reviews)
    avg = sum(r["rating"] for r in reviews)/total if total else 0
    desc = f"⭐ **Rating:** {avg:.1f}/5.0 | **Total Ulasan:** {total} Pembeli | **Total Omset:** {fmt_rp(DATA.get('total_omset',0))}\n\n🔒 Ulasan terverifikasi dari ticket DONE."
    try:
        async for msg in ch.history(limit=20):
            if msg.author == guild.me: await msg.delete()
    except: pass
    await ch.send(embed=discord.Embed(title="⭐ REPUTASI & STATISTIK — Mipi Store", description=desc, color=0xFFD700))

@tasks.loop(hours=1)
async def auto_promo():
    for guild in bot.guilds:
        ch = guild.get_channel(PROMO_CHANNEL_ID) if PROMO_CHANNEL_ID else find_channel(guild, "promosi")
        if not ch: continue
        try: await ch.send(f"🔥 **MIPI STORE BUKA!** 🔥\n🤖 Jasa Buat Bot mulai 25K | 🛠️ Setup DC mulai 25K\n🎁 Pake kode `MIPI10` buat diskon 10%!\n📦 Stok READY! Order di #🛍️・product\n💬 Testimoni: {len(DATA.get('reviews',[]))} buyer puas!")
        except: pass

# ============ TICKET JUALAN ============
async def create_ticket_filled(interaction, paket_nama, harga_str, harga_int, filled_text, extra_data=None, kode_promo=None):
    guild = interaction.guild
    cat = next((c for c in guild.categories if "ticket" in c.name.lower()), None)
    existing = discord.utils.get(guild.text_channels, name=f"ticket-{interaction.user.name.lower()}")
    if existing: return existing
    overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False), interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True), guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True)}
    channel = await guild.create_text_channel(name=f"ticket-{interaction.user.name}", category=cat, overwrites=overwrites)
    key = (extra_data or {}).get("key")
    if key in DATA.get("stok", {}): DATA["stok"][key] = max(0, DATA["stok"][key]-1)
    save_data(DATA)
    embed = discord.Embed(title="🎫 TICKET MIPI STORE", description=f"Halo {interaction.user.mention}!\n\nKamu order **{paket_nama}** 💖\n\n{filled_text}\n\n**Total Bayar:** {harga_str}\n" + (f"🎟️ Promo `{kode_promo}` kepake!\n" if kode_promo else "") + f"\n**Cara Bayar:**\n1. Scan QRIS di bawah\n2. Kirim bukti TF di sini\n3. Pencet tombol [📤 Kirim Bukti Bayar] di bawah!\n\n**Cek Progress:** Ketik `/status-pesanan` kapan aja!", color=0xFF69B4)
    embed.set_image(url=QRIS_URL)
    await channel.send(embed=embed, view=TicketActionView())
    PENDING[channel.id] = {"customer_id": interaction.user.id, "customer_mention": interaction.user.mention, "customer_name": str(interaction.user), "avatar": str(interaction.user.display_avatar.url), "produk": paket_nama, "harga": harga_str, "harga_int": harga_int, "roblox_user": (extra_data or {}).get("roblox_user", "-"), "jumlah": "1 Unit", "key": key, "kode_promo": kode_promo, "referral_by": (extra_data or {}).get("referral_by"), "progress": 0, "catatan": ""}
    return channel

class TicketActionView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    def is_allowed(self, interaction, cid):
        if interaction.user.guild_permissions.manage_channels or interaction.user.guild_permissions.administrator: return True
        d = PENDING.get(cid, {})
        return d.get("customer_id") == interaction.user.id
    @discord.ui.button(label="📤 Kirim Bukti Bayar", style=discord.ButtonStyle.blurple, custom_id="ticket_bukti")
    async def bukti(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.is_allowed(interaction, interaction.channel.id):
            await interaction.response.send_message("❌ Bukan ticket kamu!", ephemeral=True); return
        await interaction.response.send_modal(BuktiModal(interaction.channel.id))
    @discord.ui.button(label="✅ Tandai Selesai / DONE", style=discord.ButtonStyle.green, custom_id="ticket_done")
    async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.is_allowed(interaction, interaction.channel.id):
            await interaction.response.send_message("❌ Bukan ticket kamu!", ephemeral=True); return
        await interaction.response.send_modal(ReviewModal(interaction.channel.id))
    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.is_allowed(interaction, interaction.channel.id):
            await interaction.response.send_message("❌ Bukan ticket kamu!", ephemeral=True); return
        await interaction.response.send_message("Ticket ditutup dalam 5 detik...")
        await asyncio.sleep(5)
        try: await interaction.channel.delete()
        except: pass

class BuktiModal(discord.ui.Modal, title="Kirim Bukti Bayar"):
    def __init__(self, cid):
        super().__init__(); self.cid = cid
        self.link = discord.ui.TextInput(label="Link Bukti / Nama Pengirim", placeholder="Contoh: Rafix - BCA / Link foto", required=True)
        self.add_item(self.link)
    async def on_submit(self, interaction: discord.Interaction):
        d = PENDING.get(self.cid, {})
        if self.cid in PENDING: PENDING[self.cid]["progress"] = 1
        await interaction.response.send_message(f"✅ Bukti diterima! Admin bakal cek & konfirmasi. Tunggu ya!\nBukti: {self.link.value}\n\nCek status: `/status-pesanan`", ephemeral=False)
        try:
            owner = interaction.guild.owner
            if owner: await owner.send(f"💰 **PEMBAYARAN BARU!**\nTicket: {interaction.channel.mention}\nBuyer: {d.get('customer_mention')}\nProduk: {d.get('produk')}\nTotal: {d.get('harga')}\nBukti: {self.link.value}")
        except: pass

class ReviewModal(discord.ui.Modal):
    def __init__(self, cid):
        super().__init__(title="Kasih Rating & Ulasan"); self.cid = cid
        self.rating_input = discord.ui.TextInput(label="Rating (1-5)", placeholder="5", required=True, max_length=1)
        self.ulasan_input = discord.ui.TextInput(label="Ulasan / Review", placeholder="great store, fast respon!", required=True, style=discord.TextStyle.paragraph)
        self.add_item(self.rating_input); self.add_item(self.ulasan_input)
    async def on_submit(self, interaction: discord.Interaction):
        try: rating = max(1, min(5, int(self.rating_input.value.strip())))
        except: rating = 5
        ulasan = self.ulasan_input.value.strip(); tanggal = datetime.now().strftime("%d %b %Y").upper()
        d = PENDING.get(self.cid, {})
        DATA["order_count"] += 1; order_id = f"ORDER-{DATA['order_count']:06d}"
        DATA["total_omset"] = DATA.get("total_omset", 0) + d.get("harga_int", 0)
        ref = d.get("referral_by")
        if ref and ref != d.get("customer_id"):
            DATA.setdefault("affiliate", {}).setdefault(str(ref), 0)
            DATA["affiliate"][str(ref)] += int(d.get("harga_int", 0) * 0.05)
        order = {"order_id": order_id, "customer_mention": d.get("customer_mention", interaction.user.mention), "avatar": d.get("avatar"), "produk": d.get("produk", "Produk"), "harga": d.get("harga", "-"), "roblox_user": d.get("roblox_user", "-"), "jumlah": "1 Unit", "tanggal": tanggal}
        review = {"customer_mention": order["customer_mention"], "avatar": order["avatar"], "produk": order["produk"], "rating": rating, "tanggal": tanggal, "ulasan": ulasan}
        DATA.setdefault("orders", []).append(order); DATA.setdefault("reviews", []).append(review); save_data(DATA)
        guild = interaction.guild
        log_ch = find_channel(guild, "order-logs")
        if log_ch: await log_ch.send(embed=get_order_log_embed(order))
        vouch_ch = find_channel(guild, "vouch")
        if vouch_ch: await vouch_ch.send(embed=get_vouch_embed(review))
        await update_testimoni(guild)
        try: await interaction.user.send(f"🎉 Makasih udah order di MIPI STORE!\nOrder {order_id} DONE!\n\n⭐ Jangan lupa kasih testimoni lagi ya!\n🤝 Ajak temen kamu order pake ID referral kamu `{interaction.user.id}`, kamu dapet komisi 5%!\nKetik `/referral` buat liat komisi kamu!")
        except: pass
        await interaction.response.send_message(f"✅ DONE! Order **{order_id}** selesai! Ulasan masuk ke vouch & testimoni! Ticket tutup 5 detik...", ephemeral=False)
        if self.cid in PENDING: del PENDING[self.cid]
        await asyncio.sleep(5)
        try:
            ch = guild.get_channel(self.cid)
            if ch: await ch.delete()
        except: pass

class OrderBotModal(discord.ui.Modal):
    def __init__(self, key):
        super().__init__(title="Order Bot - Isi Data"); self.key = key
        self.nama_input = discord.ui.TextInput(label="Nama Kamu", placeholder="Rafix", required=True, max_length=30)
        self.jenis_input = discord.ui.TextInput(label="Jenis Bot", placeholder="Bot Store", required=True, max_length=50)
        self.fitur_input = discord.ui.TextInput(label="Fitur Yang Mau", placeholder="Welcome, Ticket, QRIS, dll", required=True, style=discord.TextStyle.paragraph)
        self.promo_input = discord.ui.TextInput(label="Kode Promo (Opsional)", placeholder="MIPI10 / kosongin aja", required=False, max_length=20)
        self.ref_input = discord.ui.TextInput(label="Kode Referral Temen (Opsional)", placeholder="ID Discord temen yang ngajak", required=False, max_length=20)
        self.add_item(self.nama_input); self.add_item(self.jenis_input); self.add_item(self.fitur_input); self.add_item(self.promo_input); self.add_item(self.ref_input)
    async def on_submit(self, interaction: discord.Interaction):
        nama, harga_int, desc = PRODUCTS_DETAIL[self.key]
        harga_final = harga_int; kode = self.promo_input.value.strip().upper() if self.promo_input.value else None; kode_valid = None
        if kode and kode in DATA.get("promo_codes", {}):
            p = DATA["promo_codes"][kode]
            if p["dipakai"] < p["max"]:
                harga_final = int(harga_int * (100 - p["diskon"]) / 100); p["dipakai"] += 1; kode_valid = kode; save_data(DATA)
        filled = f"**FORMAT ORDER (UDAH KEISI ✅):**\n```\nNama : {self.nama_input.value}\nJenis Bot : {self.jenis_input.value}\nPaket : {nama} - {fmt_rp(harga_final)}\nFitur : {self.fitur_input.value}\nHarga Awal : {fmt_rp(harga_int)}\nHarga Final : {fmt_rp(harga_final)}\n```"
        ref_id = None
        try: ref_id = int(self.ref_input.value.strip()) if self.ref_input.value.strip().isdigit() else None
        except: ref_id = None
        ch = await create_ticket_filled(interaction, f"{nama} - {fmt_rp(harga_final)}", fmt_rp(harga_final), harga_final, filled, extra_data={"nama": self.nama_input.value, "key": self.key, "referral_by": ref_id}, kode_promo=kode_valid)
        await interaction.response.send_message(f"Order dibuat! 👉 {ch.mention}\nTotal bayar: **{fmt_rp(harga_final)}**" + (f" (Diskon {kode_valid} kepake!)" if kode_valid else ""), ephemeral=True)

class OrderSetupModal(discord.ui.Modal):
    def __init__(self, key):
        super().__init__(title="Order Setup DC"); self.key = key
        self.nama_input = discord.ui.TextInput(label="Nama Kamu", placeholder="Rafix", required=True, max_length=30)
        self.server_input = discord.ui.TextInput(label="Nama Server Kamu", placeholder="MIPI STORE", required=True, max_length=30)
        self.tema_input = discord.ui.TextInput(label="Tema / Request", placeholder="Store Robux, tema pink, ticket + vouch", required=True, style=discord.TextStyle.paragraph)
        self.promo_input = discord.ui.TextInput(label="Kode Promo (Opsional)", placeholder="MIPI10", required=False)
        self.add_item(self.nama_input); self.add_item(self.server_input); self.add_item(self.tema_input); self.add_item(self.promo_input)
    async def on_submit(self, interaction: discord.Interaction):
        nama, harga_int, desc = PRODUCTS_DETAIL[self.key]
        harga_final = harga_int; kode = self.promo_input.value.strip().upper() if self.promo_input.value else None; kode_valid = None
        if kode and kode in DATA.get("promo_codes", {}):
            p = DATA["promo_codes"][kode]
            if p["dipakai"] < p["max"]:
                harga_final = int(harga_int * (100 - p["diskon"]) / 100); p["dipakai"] += 1; kode_valid = kode; save_data(DATA)
        filled = f"**FORMAT SETUP DC:**\n```\nNama : {self.nama_input.value}\nServer : {self.server_input.value}\nPaket : {nama} - {fmt_rp(harga_final)}\nTema : {self.tema_input.value}\n```"
        ch = await create_ticket_filled(interaction, f"{nama} - {fmt_rp(harga_final)}", fmt_rp(harga_final), harga_final, filled, extra_data={"nama": self.nama_input.value, "roblox_user": self.server_input.value, "key": self.key}, kode_promo=kode_valid)
        await interaction.response.send_message(f"Order dibuat! 👉 {ch.mention} Total: {fmt_rp(harga_final)}", ephemeral=True)

class OrderButton(discord.ui.View):
    def __init__(self, key): super().__init__(timeout=None); self.key = key
    @discord.ui.button(label="🛒 Order / Beli Sekarang", style=discord.ButtonStyle.green, custom_id="order_now")
    async def order_now(self, interaction: discord.Interaction, button: discord.ui.Button):
        stok = DATA.get("stok", {}).get(self.key, 99)
        if stok <= 0:
            await interaction.response.send_message("❌ Stok produk ini HABIS! Coba produk lain / tunggu restock!", ephemeral=True); return
        existing = discord.utils.get(interaction.guild.text_channels, name=f"ticket-{interaction.user.name.lower()}")
        if existing:
            await interaction.response.send_message(f"❌ Kamu udah punya ticket! 👉 {existing.mention}", ephemeral=True); return
        if self.key.startswith("setup_"): await interaction.response.send_modal(OrderSetupModal(self.key))
        else: await interaction.response.send_modal(OrderBotModal(self.key))

class CategorySelect(discord.ui.Select):
    def __init__(self, current="bot"):
        super().__init__(placeholder="🤖 Jasa Buat Bot" if current=="bot" else "🛠️ Jasa Setup DC", options=[discord.SelectOption(label="🤖 Jasa Buat Bot", value="bot", emoji="🤖"), discord.SelectOption(label="🛠️ Jasa Setup DC", value="setup", emoji="🛠️")], custom_id="cat_select")
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=CatalogLayout(self.values[0]))

class ProductSelect(discord.ui.Select):
    def __init__(self, cat_key):
        c = CATEGORIES[cat_key]; opts = []
        for label, val in c["products"]:
            stok = DATA.get("stok", {}).get(val, 99)
            opts.append(discord.SelectOption(label=f"{label} | Stok: {stok}", value=val))
        super().__init__(placeholder="🛒 Pilih Produk untuk Order...", options=opts, custom_id="prod_select")
    async def callback(self, interaction: discord.Interaction):
        key = self.values[0]; nama, harga, desc = PRODUCTS_DETAIL[key]; stok = DATA.get("stok", {}).get(key, 99)
        e = discord.Embed(title="Mipi Store CATALOG", description=f"**{nama}**\n\n**Harga:** `{fmt_rp(harga)}`\n**Stok:** `{stok} tersisa`\n**Detail:** {desc}", color=0x2B2D31)
        await interaction.response.send_message(embed=e, view=OrderButton(key), ephemeral=True)

class CatalogLayout(discord.ui.LayoutView):
    def __init__(self, cat_key="bot"):
        super().__init__(timeout=None); c = CATEGORIES[cat_key]; keys = list(CATEGORIES.keys()); idx = keys.index(cat_key)
        container = discord.ui.Container(); container.add_item(discord.ui.TextDisplay("## Mipi Store CATALOG"))
        container.add_item(discord.ui.ActionRow(CategorySelect(cat_key)))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(discord.ui.TextDisplay(f"**Kategori:** {c['kategori']}\n**⚡ Rate:** `{c['rate']}`\n**🎟️ Promo Aktif:** `MIPI10` = Diskon 10%!\n\n**List Product:**\n{c['list']}"))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(discord.ui.ActionRow(ProductSelect(cat_key)))
        row = discord.ui.ActionRow()
        prev = discord.ui.Button(label="PREV", style=discord.ButtonStyle.secondary, custom_id=f"prev_{cat_key}")
        nxt = discord.ui.Button(label="Next", style=discord.ButtonStyle.secondary, custom_id=f"next_{cat_key}")
        async def prev_cb(i: discord.Interaction, _c=cat_key):
            ks=list(CATEGORIES.keys()); await i.response.edit_message(view=CatalogLayout(ks[(ks.index(_c)-1)%len(ks)]))
        async def next_cb(i: discord.Interaction, _c=cat_key):
            ks=list(CATEGORIES.keys()); await i.response.edit_message(view=CatalogLayout(ks[(ks.index(_c)+1)%len(ks)]))
        prev.callback=prev_cb; nxt.callback=next_cb
        row.add_item(prev); row.add_item(discord.ui.Button(label=f"{idx+1}/{len(keys)}", style=discord.ButtonStyle.secondary, custom_id="page", disabled=True)); row.add_item(nxt)
        container.add_item(row); self.add_item(container)

@bot.tree.command(name="product", description="Lihat katalog produk Mipi Store")
async def product(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)
    await interaction.followup.send(view=CatalogLayout("bot"))

@bot.tree.command(name="pricelist", description="Lihat pricelist")
async def pricelist(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)
    e = discord.Embed(title="💖 PRICELIST - MIPI STORE", description="**🤖 JASA BUAT BOT**\n> SIMPLE - 25K\n> MEDIUM - 50K\n> FULL - 100K\n> PREMIUM - 150K\n> SULTAN - 250K\n> GOD - 500K\n> BOT MUSIC - 30K\n\n**🛠️ JASA SETUP DC**\n> SETUP SIMPLE - 25K\n> SETUP MEDIUM - 50K\n> SETUP FULL - 100K\n> SETUP PREMIUM - 150K\n> SETUP SULTAN - 250K\n\n🎟️ **Kode Promo:** `MIPI10` = Diskon 10%!\n*Pembayaran QRIS 💖*", color=0x2B2D31)
    await interaction.followup.send(embed=e)

# --- TICKET PANEL (DARI KODE AWAL) ---
class TicketView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🎫 Open Ticket", style=discord.ButtonStyle.blurple, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Pilih produk di #🛍️・product dulu ya!", ephemeral=True)

@bot.tree.command(name="ticket", description="Kirim panel open ticket")
async def ticket(interaction: discord.Interaction):
    try:
        await interaction.response.defer(ephemeral=False)
        embed = discord.Embed(title="MIPI STORE - OPEN!", description="**List Bisa Dibuat / Dibeli:**\n> 🤖 Jasa Buat Bot - Mulai 25K\n> 🛠️ Jasa Setup DC - Mulai 25K\n\n**Cara Order:**\n1. Ke channel `#🛍️・product` pilih produk\n2. Pencet Order -> Isi Form -> Ticket langsung keisi!\n\n*Pembayaran QRIS 💖*", color=0x2B2D31)
        await interaction.followup.send(embed=embed, view=TicketView())
    except Exception as e: print(f"ERROR ticket: {e}")

@bot.tree.command(name="referral", description="Cek komisi referral kamu")
async def referral(interaction: discord.Interaction):
    komisi = DATA.get("affiliate", {}).get(str(interaction.user.id), 0)
    await interaction.response.send_message(f"🤝 **Referral Kamu**\n\nID Referral kamu: `{interaction.user.id}`\nKasih ID ini ke temen kamu, suruh isi pas order!\n\n💰 Komisi terkumpul: **{fmt_rp(komisi)}** (5% per order temenmu)\n\nCara cairin: Buka ticket & bilang ke admin mau cairin komisi!", ephemeral=True)

@bot.tree.command(name="buat-promo", description="Buat kode promo baru (Admin)")
async def buat_promo(interaction: discord.Interaction, kode: str, diskon: int, max_pakai: int = 20):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Hanya admin!", ephemeral=True); return
    DATA.setdefault("promo_codes", {})[kode.upper()] = {"diskon": diskon, "dipakai": 0, "max": max_pakai}; save_data(DATA)
    await interaction.response.send_message(f"✅ Kode promo `{kode.upper()}` dibuat! Diskon {diskon}% | Max {max_pakai}x pakai", ephemeral=True)

@bot.tree.command(name="set-stok", description="Atur stok produk (Admin)")
async def set_stok(interaction: discord.Interaction, produk: str, jumlah: int):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Hanya admin!", ephemeral=True); return
    DATA.setdefault("stok", {})[produk] = jumlah; save_data(DATA)
    await interaction.response.send_message(f"✅ Stok `{produk}` diatur jadi {jumlah}", ephemeral=True)

@bot.tree.command(name="omset", description="Lihat total omset toko (Admin)")
async def omset(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Hanya admin!", ephemeral=True); return
    await interaction.response.send_message(f"📊 **LAPORAN MIPI STORE**\n\n💰 Total Omset: **{fmt_rp(DATA.get('total_omset',0))}**\n📦 Total Order: {len(DATA.get('orders', []))}\n⭐ Total Review: {len(DATA.get('reviews', []))}\n🎟️ Promo Aktif: {list(DATA.get('promo_codes',{}).keys())}", ephemeral=True)

@bot.tree.command(name="setup_store", description="Buat channel toko otomatis")
async def setup_store(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    cat = next((c for c in guild.categories if "catalog" in c.name.lower()), None)
    if not cat: cat = await guild.create_category("🛍️ — CATALOG —")
    for name in ["🛍️・product", "⭐・vouch", "🧾・order-logs", "⭐・testimoni", "📣・promosi", "🤖・demo-bot"]:
        if not find_channel(guild, name.split("・")[-1]):
            try: await guild.create_text_channel(name=name, category=cat)
            except: pass
    await update_testimoni(guild)
    await interaction.followup.send("✅ Berhasil! Channel product, vouch, order-logs, testimoni, promosi, demo-bot udah dibuat!", ephemeral=True)

# ============ DEMO ============
class DemoView(discord.ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)
        container = discord.ui.Container(accent_color=0x5865F2)
        container.add_item(discord.ui.TextDisplay(f"## ✦ MIPI STORE • COBA BOT DEMO GRATIS!\n✦ ───────────────────── ✦\n**Ga usah percaya kata-kata aku, COBA SENDIRI!** 👀\n\n**🎮 CARA COBA:**\n> 1. Join server demo di bawah\n> 2. Ke channel `#🤖・demo-bot`\n> 3. Ketik `/product` disana, coba semua tombolnya!\n\n**✨ YANG BISA KAMU COBA GRATIS:**\n> ✅ Buka Ticket - Rasain ticketnya keisi otomatis\n> ✅ Katalog Bot - Liat semua produk + harga\n> ✅ Middleman - Coba bikin ticket rekber\n> ✅ Check Avatar - Cek avatar Roblox kamu\n\n**⏳ GRATIS, ga perlu bayar!**\nKalo udah cocok, tinggal pencet Order di bawah!"))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        row = discord.ui.ActionRow()
        row.add_item(discord.ui.Button(label="🎮 JOIN SERVER DEMO", style=discord.ButtonStyle.link, url=DEMO_SERVER_INVITE, emoji="🎮"))
        order_btn = discord.ui.Button(label="🛒 ORDER BOT SEKARANG", style=discord.ButtonStyle.green, custom_id="demo_order")
        async def order_cb(interaction: discord.Interaction):
            await interaction.response.send_message(view=CatalogLayout("bot"), ephemeral=True)
        order_btn.callback = order_cb
        row.add_item(order_btn); container.add_item(row)
        container.add_item(discord.ui.TextDisplay("-# ✦ MIPI STORE • Coba Dulu, Baru Beli • No Tipu-Tipu"))
        self.add_item(container)

@bot.tree.command(name="demo", description="Coba bot MIPI STORE gratis sebelum beli!")
async def demo(interaction: discord.Interaction):
    await interaction.response.send_message(view=DemoView(), ephemeral=False)

@bot.tree.command(name="demo-panel", description="Kirim panel demo (Admin)")
async def demo_panel(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Hanya admin!", ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.send(view=DemoView())
    await interaction.followup.send("✅ Panel Demo dikirim!", ephemeral=True)

# ============ STATUS PESANAN ============
STATUS_LIST = [
    ("📥 PESANAN DITERIMA", "Order kamu udah masuk, admin lagi cek!"),
    ("💰 PEMBAYARAN DITERIMA", "Bukti TF udah dikonfirmasi, bot mulai digarap!"),
    ("🔨 SEDANG DIKERJAKAN", "Bot kamu lagi dibuat, sabar ya, lagi di coding!"),
    ("🧪 TESTING / REVIEW", "Bot udah jadi, lagi di test biar ga ada bug!"),
    ("✅ SELESAI / DONE", "Bot udah jadi 100%! Cek DM / Ticket kamu!"),
]
def get_status_bar(progress):
    filled = progress + 1; bar = "█" * filled + "░" * (5 - filled); persen = int(filled / 5 * 100)
    return f"`{bar}` {persen}%"
def get_status_embed(order, progress, catatan=""):
    status_nama, status_desc = STATUS_LIST[progress]
    embed = discord.Embed(title=f"📦 STATUS PESANAN - {order.get('order_id','-')}", description=f"**Halo {order.get('customer_mention','')}!**\n\n**Produk:** {order.get('produk','-')}\n**Total:** {order.get('harga','-')}\n**Tanggal Order:** {order.get('tanggal','-')}\n\n**Progress:**\n{get_status_bar(progress)}\n\n**Status Saat Ini:**\n**{status_nama}**\n{status_desc}\n", color=0xFF69B4)
    timeline = ""
    for i, (nama, _) in enumerate(STATUS_LIST):
        if i < progress: timeline += f"✅ {nama}\n"
        elif i == progress: timeline += f"🔄 **{nama}** <- KAMU DI SINI\n"
        else: timeline += f"⏳ {nama}\n"
    embed.add_field(name="📋 TIMELINE:", value=timeline, inline=False)
    if catatan: embed.add_field(name="📝 Catatan Admin:", value=catatan, inline=False)
    if progress < 4: embed.add_field(name="⏰ Estimasi Selesai:", value="1 - 3 Hari (Tergantung paket)", inline=False)
    else: embed.add_field(name="🎉", value="Makasih udah order di MIPI STORE! Jangan lupa kasih testimoni ya!", inline=False)
    return embed

@bot.tree.command(name="status-pesanan", description="Cek status pesanan bot kamu")
async def status_pesanan(interaction: discord.Interaction):
    my_orders = [o for o in DATA.get("orders", []) if o.get("customer_mention") == interaction.user.mention]
    pending_orders = []
    for cid, d in PENDING.items():
        if d.get("customer_id") == interaction.user.id:
            ch = interaction.guild.get_channel(cid)
            pending_orders.append({"order_id": f"TICKET AKTIF - #{ch.name if ch else 'ticket'}", "customer_mention": d.get("customer_mention"), "produk": d.get("produk"), "harga": d.get("harga"), "tanggal": datetime.now().strftime("%d %b %Y").upper(), "progress": d.get("progress", 0), "catatan": d.get("catatan", "")})
    if pending_orders:
        o = pending_orders[-1]
        await interaction.response.send_message(embed=get_status_embed(o, o.get("progress", 0), o.get("catatan", "")), ephemeral=True); return
    if my_orders:
        o = my_orders[-1]
        await interaction.response.send_message(embed=get_status_embed(o, 4, ""), ephemeral=True); return
    await interaction.response.send_message("❌ Kamu belum punya pesanan!\nOrder dulu di `/product` ya!", ephemeral=True)

@bot.tree.command(name="update-status", description="Update status pesanan buyer (Admin)")
async def update_status(interaction: discord.Interaction, user: discord.Member, status: int, catatan: str = ""):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Hanya admin!", ephemeral=True); return
    if status < 0 or status > 4:
        await interaction.response.send_message("❌ Status harus 0-4!\n0=Diterima, 1=Dibayar, 2=Dikerjakan, 3=Testing, 4=Selesai", ephemeral=True); return
    found = False
    for cid, d in PENDING.items():
        if d.get("customer_id") == user.id:
            d["progress"] = status; d["catatan"] = catatan; found = True
            ch = interaction.guild.get_channel(cid)
            if ch:
                dummy = {"order_id": f"ORDER-{DATA.get('order_count',0)+1:06d}", "customer_mention": d.get("customer_mention"), "produk": d.get("produk"), "harga": d.get("harga"), "tanggal": datetime.now().strftime("%d %b %Y").upper()}
                await ch.send(content=f"{user.mention} 📢 Status pesanan kamu di-update!", embed=get_status_embed(dummy, status, catatan))
            break
    if not found:
        await interaction.response.send_message(f"❌ {user.mention} ga punya ticket aktif!", ephemeral=True); return
    save_data(DATA)
    status_nama, _ = STATUS_LIST[status]
    await interaction.response.send_message(f"✅ Status {user.mention} di-update jadi **{status_nama}**\nCatatan: {catatan if catatan else '-'}", ephemeral=True)
    try: await user.send(f"📢 **STATUS PESANAN DI-UPDATE!**\n\nStatus baru kamu: **{STATUS_LIST[status][0]}**\nCatatan admin: {catatan if catatan else '-'}\n\nKetik `/status-pesanan` di server buat liat lengkapnya!")
    except: pass

@bot.tree.command(name="status-panel", description="Kirim panel status pesanan (Admin)")
async def status_panel(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Hanya admin!", ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    view = discord.ui.LayoutView(); c = discord.ui.Container(accent_color=0xFF69B4)
    c.add_item(discord.ui.TextDisplay("## ✦ MIPI STORE • STATUS PESANAN\n✦ ───────────────────── ✦\n**Penasaran bot kamu udah jadi belum?** 🤔\n\nGa perlu nanya-nanya lagi ke admin!\nKetik `/status-pesanan` aja, langsung keliatan progressnya!\n\n**📋 Progressnya:**\n> 📥 Diterima -> 💰 Dibayar -> 🔨 Dikerjakan -> 🧪 Testing -> ✅ Selesai\n\n**Cara Cek:**\n> Ketik `/status-pesanan` di channel mana aja!"))
    c.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
    c.add_item(discord.ui.TextDisplay("-# ✦ MIPI STORE • Update Otomatis Tiap Ada Progress"))
    view.add_item(c)
    await interaction.channel.send(view=view)
    await interaction.followup.send("✅ Panel Status dikirim!", ephemeral=True)

# ============ MIDDLEMAN ============
MID_FEES = {"Rp 1.000 - Rp 9.000": 1500, "Rp 10.000 - Rp 49.000": 2500, "Rp 50.000 - Rp 99.000": 4500, "Rp 100.000 - Rp 199.000": 6500, "Rp 200.000 - Rp 499.000": 10000, "Rp 500.000 - Rp 1.000.000": 15000, "Di atas Rp 1.000.000": 20000}
def get_mid_embed():
    return discord.Embed(title="Middleman/Rekber Service by MIPI STORE", description="**Daftar Fee Middleman:**\n• Rp 1.000 - Rp 9.000 -> Fee 1.500\n• Rp 10.000 - Rp 49.000 -> Fee 2.500\n• Rp 50.000 - Rp 99.000 -> Fee 4.500\n• Rp 100.000 - Rp 199.000 -> Fee 6.500\n• Rp 200.000 - Rp 499.000 -> Fee 10.000\n• Rp 500.000 - Rp 1.000.000 -> Fee 15.000\n• Di atas Rp 1.000.000 -> Fee 20.000\n\n📌 Fee dibayar 1x per transaksi\n📌 Fee bisa ditanggung buyer / seller / split\n\nKlik tombol di bawah lalu pilih buyer dan seller dari dropdown.", color=0x2B2D31)
class MiddlemanPanelView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="📜 History Transaksi", style=discord.ButtonStyle.secondary, custom_id="mid_history")
    async def history(self, interaction: discord.Interaction, button: discord.ui.Button):
        ch = find_channel(interaction.guild, "vouch")
        await interaction.response.send_message(f"Cek history di {ch.mention if ch else 'vouch'} ya!", ephemeral=True)
    @discord.ui.button(label="🛡️ Buat Ticket Middleman", style=discord.ButtonStyle.primary, custom_id="mid_create")
    async def create_mid(self, interaction: discord.Interaction, button: discord.ui.Button):
        existing = discord.utils.get(interaction.guild.text_channels, name=f"mid-{interaction.user.name.lower()}")
        if existing:
            await interaction.response.send_message(f"❌ Udah punya ticket! 👉 {existing.mention}", ephemeral=True); return
        await interaction.response.send_message(embed=get_mid_form_embed(interaction.user.id), view=MiddlemanFormView(interaction.user.id), ephemeral=True)
def get_mid_form_embed(uid):
    d = MID_PENDING.get(uid, {})
    return discord.Embed(title="🎫 Ticket Middleman", description=f"• Rentang: {d.get('rentang','-')}\n• Fee: {d.get('fee','-')}\n• Buyer: {d.get('buyer_mention','-')}\n• Seller: {d.get('seller_mention','-')}\n• Fee Ditanggung: {d.get('ditanggung','-')}\n• Jenis: {d.get('jenis','-')}\n• Harga: {d.get('harga','-')}", color=0x2B2D31)
class RentangSelect(discord.ui.Select):
    def __init__(self, uid): super().__init__(placeholder="Pilih rentang transaksi", options=[discord.SelectOption(label=k, value=k) for k in MID_FEES.keys()]); self.uid=uid
    async def callback(self, interaction: discord.Interaction):
        d=MID_PENDING.setdefault(self.uid,{}); d["rentang"]=self.values[0]; d["fee"]=fmt_rp(MID_FEES[self.values[0]])
        await interaction.response.edit_message(embed=get_mid_form_embed(self.uid), view=MiddlemanFormView(self.uid))
class BuyerSelect(discord.ui.UserSelect):
    def __init__(self, uid): super().__init__(placeholder="Pilih buyer"); self.uid=uid
    async def callback(self, interaction: discord.Interaction):
        d=MID_PENDING.setdefault(self.uid,{}); d["buyer_id"]=self.values[0].id; d["buyer_mention"]=self.values[0].mention
        await interaction.response.edit_message(embed=get_mid_form_embed(self.uid), view=MiddlemanFormView(self.uid))
class SellerSelect(discord.ui.UserSelect):
    def __init__(self, uid): super().__init__(placeholder="Pilih seller"); self.uid=uid
    async def callback(self, interaction: discord.Interaction):
        d=MID_PENDING.setdefault(self.uid,{}); d["seller_id"]=self.values[0].id; d["seller_mention"]=self.values[0].mention
        await interaction.response.edit_message(embed=get_mid_form_embed(self.uid), view=MiddlemanFormView(self.uid))
class FeePayerSelect(discord.ui.Select):
    def __init__(self, uid): super().__init__(placeholder="Fee ditanggung oleh...", options=[discord.SelectOption(label="Buyer", value="Buyer"), discord.SelectOption(label="Seller", value="Seller"), discord.SelectOption(label="Split", value="Split")]); self.uid=uid
    async def callback(self, interaction: discord.Interaction):
        d=MID_PENDING.setdefault(self.uid,{}); d["ditanggung"]=self.values[0]
        await interaction.response.edit_message(embed=get_mid_form_embed(self.uid), view=MiddlemanFormView(self.uid))
class MidDetailModal(discord.ui.Modal, title="Isi Detail Barang"):
    def __init__(self, uid):
        super().__init__(); self.uid=uid
        self.jenis_input = discord.ui.TextInput(label="Jenis Barang", placeholder="Akun Roblox / Robux", required=True)
        self.harga_input = discord.ui.TextInput(label="Harga Barang", placeholder="Rp 50.000", required=True)
        self.add_item(self.jenis_input); self.add_item(self.harga_input)
    async def on_submit(self, interaction: discord.Interaction):
        d=MID_PENDING.setdefault(self.uid,{}); d["jenis"]=self.jenis_input.value; d["harga"]=self.harga_input.value
        await interaction.response.edit_message(embed=get_mid_form_embed(self.uid), view=MiddlemanFormView(self.uid))
class MiddlemanFormView(discord.ui.View):
    def __init__(self, uid):
        super().__init__(timeout=600); self.uid=uid
        self.add_item(RentangSelect(uid)); self.add_item(BuyerSelect(uid)); self.add_item(SellerSelect(uid)); self.add_item(FeePayerSelect(uid))
    @discord.ui.button(label="Saya = Buyer", style=discord.ButtonStyle.secondary, custom_id="mid_i_buyer", row=4)
    async def i_buyer(self, interaction: discord.Interaction, button: discord.ui.Button):
        d=MID_PENDING.setdefault(self.uid,{}); d["buyer_id"]=interaction.user.id; d["buyer_mention"]=interaction.user.mention
        await interaction.response.edit_message(embed=get_mid_form_embed(self.uid), view=MiddlemanFormView(self.uid))
    @discord.ui.button(label="📝 Isi Detail", style=discord.ButtonStyle.primary, custom_id="mid_detail", row=4)
    async def detail(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(MidDetailModal(self.uid))
    @discord.ui.button(label="✅ Buat Ticket", style=discord.ButtonStyle.green, custom_id="mid_buat", row=4)
    async def buat(self, interaction: discord.Interaction, button: discord.ui.Button):
        d=MID_PENDING.get(self.uid,{})
        if not d.get("rentang") or not d.get("buyer_mention") or not d.get("seller_mention") or not d.get("ditanggung"):
            await interaction.response.send_message("❌ Lengkapi dulu!", ephemeral=True); return
        guild=interaction.guild; cat=next((c for c in guild.categories if "ticket" in c.name.lower()), None)
        overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=False), guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True), interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        for uid in [d.get("buyer_id"), d.get("seller_id")]:
            m=guild.get_member(uid) if uid else None
            if m: overwrites[m]=discord.PermissionOverwrite(view_channel=True, send_messages=True)
        ch=await guild.create_text_channel(name=f"mid-{interaction.user.name.lower()}", category=cat, overwrites=overwrites)
        e=discord.Embed(title="🛡️ TICKET MIDDLEMAN - MIPI STORE", description=f"Buyer: {d.get('buyer_mention')} | Seller: {d.get('seller_mention')}\n\nRentang: {d.get('rentang')}\nFee: {d.get('fee')}\nDitanggung: {d.get('ditanggung')}\nBarang: {d.get('jenis','-')} - {d.get('harga','-')}\n\n1. Buyer TF ke Admin\n2. Seller kirim barang\n3. Buyer konfirmasi\n4. Admin terusin dana ke Seller", color=0x2B2D31)
        await ch.send(content=f"{d.get('buyer_mention')} {d.get('seller_mention')}", embed=e, view=MidTicketActionView())
        if self.uid in MID_PENDING: del MID_PENDING[self.uid]
        await interaction.response.send_message(f"✅ Ticket dibuat! 👉 {ch.mention}", ephemeral=True)
    @discord.ui.button(label="❌ Batal", style=discord.ButtonStyle.red, custom_id="mid_batal", row=4)
    async def batal(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.uid in MID_PENDING: del MID_PENDING[self.uid]
        await interaction.response.edit_message(content="❌ Dibatalkan.", embed=None, view=None)
class MidTicketActionView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="✅ DONE", style=discord.ButtonStyle.green, custom_id="mid_done")
    async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Hanya admin!", ephemeral=True); return
        await interaction.response.send_message("✅ Middleman SELESAI! Tutup 5 detik..."); await asyncio.sleep(5)
        try: await interaction.channel.delete()
        except: pass
    @discord.ui.button(label="🔒 Close", style=discord.ButtonStyle.red, custom_id="mid_close")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Hanya admin!", ephemeral=True); return
        await interaction.response.send_message("Tutup 5 detik..."); await asyncio.sleep(5)
        try: await interaction.channel.delete()
        except: pass

@bot.tree.command(name="middleman-panel", description="Kirim panel Middleman")
async def middleman_panel(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Hanya admin!", ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.send(embed=get_mid_embed(), view=MiddlemanPanelView())
    await interaction.followup.send("✅ Panel Middleman dikirim!", ephemeral=True)

@bot.tree.command(name="setup-middleman", description="Bikin channel middleman otomatis")
async def setup_middleman(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Hanya admin!", ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    guild=interaction.guild; ch=next((c for c in guild.text_channels if "midman" in c.name.lower() or "rekber" in c.name.lower()), None)
    if not ch: ch=await guild.create_text_channel("🎫・ticket-midman-rekber")
    await ch.send(embed=get_mid_embed(), view=MiddlemanPanelView())
    await interaction.followup.send(f"✅ Panel di {ch.mention}!", ephemeral=True)

# ============ CHECK AVATAR + CEK RBX (DARI KODE AWAL) ============
async def get_rbx_user_id(s, u):
    async with s.post("https://users.roblox.com/v1/usernames/users", json={"usernames":[u], "excludeBannedUsers": False}) as r:
        d=await r.json(); return d["data"][0]["id"] if d.get("data") else None
async def get_rbx_user_info(s, uid):
    async with s.get(f"https://users.roblox.com/v1/users/{uid}") as r: return await r.json()
async def get_rbx_avatar(s, uid):
    async with s.get(f"https://thumbnails.roblox.com/v1/users/avatar?userIds={uid}&size=420x420&format=Png&isCircular=false") as r:
        d=await r.json(); return d["data"][0]["imageUrl"] if d.get("data") else None
async def get_rbx_avatar_details(s, uid):
    try:
        async with s.get(f"https://avatar.roblox.com/v1/users/{uid}/avatar") as r:
            d=await r.json(); return d.get("assets", [])
    except: return []
BUANG_KATA=["animation","animasi","bundle","billie","run","walk","jump","climb","fall","swim","idle","tubuh","wajah","torso","leg","arm","head","face","smile","mood","default","classic"]
def filter_item_bagus(assets):
    hasil=[]; seen=set()
    for a in assets:
        aid=a.get("id"); nama=(a.get("name") or "").strip()
        if not aid or not nama: continue
        nl=nama.lower()
        if any(k in nl for k in BUANG_KATA): continue
        if nl in seen: continue
        seen.add(nl); hasil.append(a)
        if len(hasil)>=10: break
    return hasil
async def kirim_hasil_checkavatar(interaction, username):
    try:
        if not interaction.response.is_done(): await interaction.response.defer(ephemeral=False)
    except: pass
    try:
        async with aiohttp.ClientSession() as s:
            uid=await get_rbx_user_id(s, username)
            if not uid:
                await interaction.followup.send(f"❌ Username **{username}** ga ketemu!", ephemeral=True); return
            info=await get_rbx_user_info(s, uid); avatar_url=await get_rbx_avatar(s, uid); assets=await get_rbx_avatar_details(s, uid)
            tampil=filter_item_bagus(assets)
            teks="### 👗 Item Yang Dipake\n" + ("".join([f"> [{a.get('name')}](https://www.roblox.com/catalog/{a.get('id')})\n" for a in tampil]) if tampil else "> Avatar default / tidak terbaca.")
            bio=info.get('description') or 'Tidak ada bio'
            if len(bio)>120: bio=bio[:120]+"..."
            view=discord.ui.LayoutView(); c=discord.ui.Container(accent_color=0xFF69B4)
            c.add_item(discord.ui.TextDisplay(f"## ✦ MIPI STORE • CHECK AVATAR\n**👤 Username:** `{info.get('name')}`\n**✨ Display:** `{info.get('displayName')}`\n**🆔 ID:** `{uid}`\n**📝 Bio:** {bio}\nDi-cek sama {interaction.user.mention}"))
            c.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
            if avatar_url: c.add_item(discord.ui.MediaGallery(discord.MediaGalleryItem(media=avatar_url)))
            c.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small)); c.add_item(discord.ui.TextDisplay(teks))
            row=discord.ui.ActionRow(); row.add_item(discord.ui.Button(label="Buka Profil Roblox", style=discord.ButtonStyle.link, url=f"https://www.roblox.com/users/{uid}/profile", emoji="👤")); c.add_item(row)
            view.add_item(c); await interaction.followup.send(view=view)
    except Exception as e: print(e)

class CheckAvatarModal(discord.ui.Modal, title="Check Avatar Roblox"):
    username_input = discord.ui.TextInput(label="Username Roblox", placeholder="1mrafii", required=True, max_length=20)
    async def on_submit(self, interaction: discord.Interaction): await kirim_hasil_checkavatar(interaction, self.username_input.value.strip())

class CheckRbxModal(discord.ui.Modal, title="Cek RBX / Gamepass"):
    username_input = discord.ui.TextInput(label="Username Roblox", placeholder="Contoh: DENCOW2505", required=True, max_length=20)
    link_input = discord.ui.TextInput(label="Link Gamepass (Opsional)", placeholder="https://www.roblox.com/game-pass/...", required=False, max_length=100)
    async def on_submit(self, interaction: discord.Interaction):
        username = self.username_input.value.strip(); link = self.link_input.value.strip()
        await interaction.response.send_message(f"## Mipi Store CHECK\n**Username :** {username}\n**Gamepass :** {link if link else 'Tidak diisi'}\n\nCek di Roblox > Revenue > Pending Sales ya!\nRoblox hold Robux **3 - 7 hari**, itu normal.\n\nMIPI STORE • Aman, Cepat, Terpercaya", ephemeral=True)

class CheckAvatarPanelLayout(discord.ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None); c=discord.ui.Container(accent_color=0xFF69B4)
        c.add_item(discord.ui.TextDisplay("## ✦ MIPI STORE • CHECK AVATAR\n**Halo!** 💖 Liat avatar Roblox kamu di sini!\n\n> Pencet tombol di bawah\n> Ketik username Roblox kamu\n> Langsung muncul avatar + item"))
        c.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        row=discord.ui.ActionRow(); btn=discord.ui.Button(label="CEK AVATAR", style=discord.ButtonStyle.primary, emoji="🔍", custom_id="cek_avatar_pencet")
        async def cb(i: discord.Interaction): await i.response.send_modal(CheckAvatarModal())
        btn.callback=cb; row.add_item(btn); c.add_item(row); self.add_item(c)

class CheckRbxPanelLayout(discord.ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)
        container = discord.ui.Container(accent_color=0xFFD700)
        container.add_item(discord.ui.TextDisplay(f"## ✦ MIPI STORE • CEK RBX\n✦ ───────────────────── ✦\n**Halo, mau cek Robux kamu?** 💰\n\nCek Robux kamu udah masuk / masih pending di sini.\n\n**✨ Cara Pakai :**\n> Pencet tombol di bawah\n> Ketik username + link gamepass\n> Kirim, langsung kecek\n✦ ───────────────────── ✦"))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        row_top = discord.ui.ActionRow()
        row_top.add_item(discord.ui.Button(label="CEK RBX / GAMEPASS", style=discord.ButtonStyle.secondary, custom_id="cat_rbx", disabled=True, emoji="✦"))
        container.add_item(row_top)
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(discord.ui.TextDisplay(f"**Kategori :** 💰 Cek RBX / Gamepass\n**Fungsi :** Cek pending Robux\n**Status :** 🟢 Online"))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        row_main = discord.ui.ActionRow()
        btn = discord.ui.Button(label="CEK RBX", style=discord.ButtonStyle.success, emoji="💰", custom_id="cek_rbx_pencet")
        async def rbx_cb(interaction: discord.Interaction):
            await interaction.response.send_modal(CheckRbxModal())
        btn.callback = rbx_cb
        row_main.add_item(btn)
        container.add_item(row_main)
        container.add_item(discord.ui.TextDisplay("-# ✦ MIPI STORE • Tinggal Pencet Aja!"))
        self.add_item(container)

@bot.tree.command(name="checkavatar", description="Cek avatar Roblox")
async def checkavatar(interaction: discord.Interaction, username: str): await kirim_hasil_checkavatar(interaction, username)

@bot.tree.command(name="cekrbx", description="Cek RBX / Gamepass")
async def cekrbx(interaction: discord.Interaction, username: str = None, link_gamepass: str = None):
    try:
        if not username:
            await interaction.response.send_modal(CheckRbxModal()); return
        await interaction.response.send_message(f"## Mipi Store CHECK\n**Username :** {username}\n**Gamepass :** {link_gamepass or 'Tidak diisi'}\n\nCek di Roblox > Revenue > Pending Sales ya!\nRoblox hold Robux **3 - 7 hari**, itu normal.", ephemeral=True)
    except Exception as e: print(f"ERROR cekrbx: {e}")

@bot.tree.command(name="checkavatar-panel", description="Kirim panel cek avatar (Owner only)")
async def checkavatar_panel(interaction: discord.Interaction):
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ Hanya Owner!", ephemeral=True); return
    await interaction.response.defer(ephemeral=True); await interaction.followup.send(view=CheckAvatarPanelLayout())
    await interaction.followup.send("✅ Panel Check Avatar berhasil dikirim!", ephemeral=True)

@bot.tree.command(name="cekrbx-panel", description="Kirim panel cek rbx (Owner only)")
async def cekrbx_panel(interaction: discord.Interaction):
    try:
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ Hanya Owner!", ephemeral=True); return
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(view=CheckRbxPanelLayout())
        await interaction.followup.send("✅ Panel Cek RBX berhasil dikirim!", ephemeral=True)
    except Exception as e: print(f"ERROR cekrbx-panel: {e}")

@bot.tree.command(name="setup-cek", description="Bikin channel cek avatar + cek rbx (Owner only)")
async def setup_cek(interaction: discord.Interaction):
    try:
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ Hanya Owner!", ephemeral=True); return
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        for ch in list(guild.channels):
            if ch.name in ["check-avatar", "cek-rbx", "hasil-check", "🔍┆・check-avatar", "💰┆・cek-rbx", "✅┆・hasil-check", "✦┆・verifikasi", "✅┆・verifikasi"]:
                try: await ch.delete()
                except: pass
        ch1 = await guild.create_text_channel("🔍┆・check-avatar")
        ch2 = await guild.create_text_channel("💰┆・cek-rbx")
        msg = await ch1.send(view=CheckAvatarPanelLayout())
        try: await msg.pin()
        except: pass
        await ch2.send(view=CheckRbxPanelLayout())
        await interaction.followup.send(f"✅ Berhasil! {ch1.mention} + {ch2.mention} udah dibuat!\nPanel di {ch1.mention} cuma di-pin 1x, ga auto hapus lagi jadi ga ngebug!", ephemeral=True)
    except Exception as e: print(f"ERROR setup-cek: {e}")

@bot.event
async def setup_hook():
    try:
        bot.add_view(CheckAvatarPanelLayout()); bot.add_view(CheckRbxPanelLayout()); bot.add_view(TicketActionView()); bot.add_view(MiddlemanPanelView()); bot.add_view(MidTicketActionView()); bot.add_view(DemoView()); bot.add_view(TicketView())
        print("Persistent views OK - SEMUA PANEL AKTIF")
    except Exception as e: print(e)

bot.run(os.getenv("DISCORD_TOKEN"))

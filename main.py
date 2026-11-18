import discord
from discord.ext import commands
import os
import json
import time
import asyncio
import aiohttp
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

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"order_count": 0, "reviews": [], "orders": []}

def save_data(data):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except:
        pass

DATA = load_data()
PENDING = {}
COOLDOWN = {}

@bot.event
async def on_ready():
    print(f"Bot Online: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)

CATEGORIES = {
    "bot": {
        "kategori": "Jasa Buat Bot",
        "rate": "Mulai Rp 25.000",
        "list": "• SIMPLE\n  └ 🏷️ Rp 25.000\n• MEDIUM\n  └ 🏷️ Rp 50.000\n• FULL\n  └ 🏷️ Rp 100.000\n• PREMIUM\n  └ 🏷️ Rp 150.000\n• SULTAN\n  └ 🏷️ Rp 250.000\n• GOD\n  └ 🏷️ Rp 500.000\n• BOT MUSIC\n  └ 🏷️ Rp 30.000",
        "products": [
            ("💎 SIMPLE - Rp 25.000", "simple"),
            ("🛡️ MEDIUM - Rp 50.000", "medium"),
            ("⭐ FULL - Rp 100.000", "full"),
            ("👑 PREMIUM - Rp 150.000", "premium"),
            ("🔥 SULTAN - Rp 250.000", "sultan"),
            ("🧊 GOD - Rp 500.000", "god"),
            ("🎵 BOT MUSIC - Rp 30.000", "music"),
        ]
    },
    "setup": {
        "kategori": "Jasa Setup DC",
        "rate": "Mulai Rp 25.000",
        "list": "• SETUP SIMPLE\n  └ 🏷️ Rp 25.000\n• SETUP MEDIUM\n  └ 🏷️ Rp 50.000\n• SETUP FULL\n  └ 🏷️ Rp 100.000\n• SETUP PREMIUM\n  └ 🏷️ Rp 150.000\n• SETUP SULTAN\n  └ 🏷️ Rp 250.000",
        "products": [
            ("🛠️ SETUP SIMPLE - Rp 25.000", "setup_simple"),
            ("🛠️ SETUP MEDIUM - Rp 50.000", "setup_medium"),
            ("🛠️ SETUP FULL - Rp 100.000", "setup_full"),
            ("🛠️ SETUP PREMIUM - Rp 150.000", "setup_premium"),
            ("🛠️ SETUP SULTAN - Rp 250.000", "setup_sultan"),
        ]
    },
}

PRODUCTS_DETAIL = {
    "simple": ("💎 SIMPLE", "Rp 25.000", "Ticket + QRIS + Status + Close"),
    "medium": ("🛡️ MEDIUM", "Rp 50.000", "Simple + Saldo + Leaderboard + Vouch + Giveaway"),
    "full": ("⭐ FULL", "Rp 100.000", "Medium + Promo + Anti Jualan + History + 7 Produk + Custom + Diajarin Sampai Bisa"),
    "premium": ("👑 PREMIUM", "Rp 150.000", "Semua Full + 7 Fitur Custom + Setup Hosting + Support Lifetime"),
    "sultan": ("🔥 SULTAN", "Rp 250.000", "Semua Premium + 5 Fitur Custom + 2 Bot + Banner Gratis + VIP"),
    "god": ("🧊 GOD", "Rp 500.000", "Semua Sultan + Unlimited + Source Code + Partner MIPI"),
    "music": ("🎵 BOT MUSIC", "Rp 30.000", "Music 24/7 + Play / Skip / Queue + Spotify & Youtube"),
    "setup_simple": ("🛠️ SETUP SIMPLE", "Rp 25.000", "Channel + Role + Kategori + Rules"),
    "setup_medium": ("🛠️ SETUP MEDIUM", "Rp 50.000", "Simple + Ticket + Welcome + Vouch + Pricelist"),
    "setup_full": ("🛠️ SETUP FULL", "Rp 100.000", "Medium + Bot Ticket + Leaderboard + Banner + Catalog"),
    "setup_premium": ("🛠️ SETUP PREMIUM", "Rp 150.000", "Semua Full + Custom Design + Setup Hosting + Support 7 Hari"),
    "setup_sultan": ("🛠️ SETUP SULTAN", "Rp 250.000", "Semua Premium + 2 Bot + Banner Gratis + VIP + Support Lifetime"),
}

def find_channel(guild, name_part):
    if "vouch" in name_part.lower():
        ch = guild.get_channel(VOUCH_CHANNEL_ID)
        if ch:
            return ch
    if "order-logs" in name_part.lower():
        ch = guild.get_channel(ORDER_LOGS_CHANNEL_ID)
        if ch:
            return ch
    if "testimoni" in name_part.lower():
        ch = guild.get_channel(TESTIMONI_CHANNEL_ID)
        if ch:
            return ch
    for ch in guild.text_channels:
        if name_part in ch.name.lower():
            return ch
    return None

def get_vouch_embed(review):
    embed = discord.Embed(title="⭐ TESTIMONI PEMBELI — Mipi Store", color=0xFFD700)
    embed.add_field(name="👤 Pembeli:", value=review["customer_mention"], inline=False)
    embed.add_field(name="📦 Produk:", value=review["produk"], inline=False)
    embed.add_field(name="⭐ Rating:", value=f"{'⭐' * review['rating']} ({review['rating']}/5)", inline=False)
    embed.add_field(name="📅 Tanggal:", value=review["tanggal"], inline=False)
    embed.add_field(name="💬 Ulasan & Review:", value=f"\"{review['ulasan']}\"", inline=False)
    if review.get("avatar"):
        embed.set_thumbnail(url=review["avatar"])
    return embed

def get_order_log_embed(order):
    embed = discord.Embed(title=f"🧾 ORDER LOG — {order['order_id']}", color=0x2B2D31)
    embed.add_field(name="👤 Customer:", value=order["customer_mention"], inline=False)
    embed.add_field(name="🎮 Nama Server:", value=order.get("roblox_user", "-"), inline=False)
    embed.add_field(name="📦 Produk:", value=order["produk"], inline=False)
    embed.add_field(name="📦 Jumlah:", value=order.get("jumlah", "1 Unit"), inline=False)
    embed.add_field(name="💰 Total Bayar:", value=order["harga"], inline=False)
    embed.add_field(name="💳 Metode:", value="QRIS (All Payment)", inline=False)
    embed.add_field(name="📅 Tanggal:", value=order["tanggal"], inline=False)
    embed.add_field(name="📊 Status:", value="🟢 DONE / PAID", inline=False)
    if order.get("avatar"):
        embed.set_thumbnail(url=order["avatar"])
    return embed

def get_testimoni_embed():
    reviews = DATA.get("reviews", [])
    total = len(reviews)
    avg = sum(r["rating"] for r in reviews) / total if total > 0 else 0.0
    counts = {5:0, 4:0, 3:0, 2:0, 1:0}
    for r in reviews:
        counts[r["rating"]] = counts.get(r["rating"], 0) + 1
    stars = "⭐" * round(avg) if avg > 0 else "⭐"
    desc = f"Rangkuman kepuasan dan ulasan pelanggan dari transaksi terverifikasi di Mipi Store:\n\n"
    desc += f"📊 **STATISTIK REPUTASI TOKO:**\n"
    desc += f"⭐ **Rating Kepuasan:** {avg:.1f} / 5.0 {stars}\n"
    desc += f"⭐ **Total Ulasan Selesai:** {total} Pembeli\n\n"
    desc += f"📝 **RINCIAN RATING BINTANG:**\n"
    desc += f"⭐⭐⭐⭐⭐ (5 Bintang): {counts[5]} ulasan\n"
    desc += f"⭐⭐⭐⭐ (4 Bintang): {counts[4]} ulasan\n"
    desc += f"⭐⭐⭐ (3 Bintang): {counts[3]} ulasan\n"
    desc += f"⭐⭐ (2 Bintang): {counts[2]} ulasan\n"
    desc += f"⭐ (1 Bintang): {counts[1]} ulasan\n\n"
    desc += f"🔒 *Reputasi Terverifikasi Otomatis: Setiap ulasan di bawah berasal langsung dari tiket pesanan yang telah selesai (DONE).*"
    embed = discord.Embed(title="⭐ REPUTASI & STATISTIK TOKO — Mipi Store", description=desc, color=0xFFD700)
    return embed

async def update_testimoni_channel(guild):
    ch = find_channel(guild, "testimoni")
    if not ch:
        return
    try:
        async for msg in ch.history(limit=20):
            if msg.author == guild.me:
                try:
                    await msg.delete()
                except:
                    pass
    except:
        pass
    await ch.send(embed=get_testimoni_embed())

async def create_ticket_filled(interaction, paket_nama, harga, filled_text, extra_data=None):
    guild = interaction.guild
    category = None
    for cat in guild.categories:
        if "ticket" in cat.name.lower():
            category = cat
            break
    existing = discord.utils.get(guild.text_channels, name=f"ticket-{interaction.user.name.lower()}")
    if existing:
        return existing
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True),
    }
    channel = await guild.create_text_channel(name=f"ticket-{interaction.user.name}", category=category, overwrites=overwrites)
    embed = discord.Embed(title="🎫 TICKET MIPI STORE", description=f"Halo {interaction.user.mention}!\n\nKamu order **{paket_nama}** 💖\n\n{filled_text}\n\nPembayaran via **QRIS** ya! Scan di bawah ini, terus kirim bukti TF di sini 👇", color=0xFF69B4)
    embed.set_image(url="https://raw.githubusercontent.com/mipistore/mipi-store/main/IMG_5210.jpeg")
    await channel.send(embed=embed, view=TicketActionView())
    PENDING[channel.id] = {
        "customer_id": interaction.user.id,
        "customer_mention": interaction.user.mention,
        "customer_name": str(interaction.user),
        "avatar": str(interaction.user.display_avatar.url) if interaction.user.display_avatar else None,
        "produk": paket_nama,
        "harga": harga,
        "roblox_user": (extra_data or {}).get("roblox_user", "-"),
        "nama": (extra_data or {}).get("nama", "-"),
        "jumlah": (extra_data or {}).get("jumlah", "1 Unit"),
    }
    return channel

class TicketActionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    def is_allowed(self, interaction, channel_id):
        if interaction.user.guild_permissions.manage_channels or interaction.user.guild_permissions.administrator:
            return True
        data = PENDING.get(channel_id, {})
        if data.get("customer_id") == interaction.user.id:
            return True
        ch_name = interaction.channel.name.lower() if interaction.channel else ""
        if ch_name.startswith("ticket-"):
            owner_name = ch_name.replace("ticket-", "").strip()
            if interaction.user.name.lower() == owner_name:
                return True
        return False
    @discord.ui.button(label="✅ Tandai Selesai / DONE", style=discord.ButtonStyle.green, custom_id="ticket_done")
    async def ticket_done(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.is_allowed(interaction, interaction.channel.id):
            await interaction.response.send_message("❌ Ehh, ini bukan ticket kamu! Cuma pemilik ticket + admin yang bisa pencet DONE!", ephemeral=True)
            return
        await interaction.response.send_modal(ReviewModal(interaction.channel.id))
    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.is_allowed(interaction, interaction.channel.id):
            await interaction.response.send_message("❌ Ehh, ini bukan ticket kamu! Cuma pemilik ticket + admin yang bisa Close!", ephemeral=True)
            return
        await interaction.response.send_message("Ticket akan ditutup dalam 5 detik...")
        await interaction.channel.delete()

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket2")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Ticket akan ditutup dalam 5 detik...")
        await interaction.channel.delete()

class ReviewModal(discord.ui.Modal):
    def __init__(self, channel_id):
        super().__init__(title="Kasih Rating & Ulasan")
        self.channel_id = channel_id
        self.rating_input = discord.ui.TextInput(label="Rating (1-5)", placeholder="Contoh: 5", required=True, max_length=1)
        self.ulasan_input = discord.ui.TextInput(label="Ulasan / Review", placeholder="Contoh: great store, fast respon!", required=True, style=discord.TextStyle.paragraph)
        self.add_item(self.rating_input)
        self.add_item(self.ulasan_input)
    async def on_submit(self, interaction: discord.Interaction):
        try:
            rating = int(self.rating_input.value.strip())
            if rating < 1: rating = 1
            if rating > 5: rating = 5
        except:
            rating = 5
        ulasan = self.ulasan_input.value.strip()
        tanggal = datetime.now().strftime("%d %b %Y").upper()
        data = PENDING.get(self.channel_id, {})
        customer_mention = data.get("customer_mention", interaction.user.mention)
        avatar = data.get("avatar", str(interaction.user.display_avatar.url))
        produk = data.get("produk", "Produk Mipi Store")
        harga = data.get("harga", "-")
        roblox_user = data.get("roblox_user", "-")
        jumlah = data.get("jumlah", "1 Unit")
        DATA["order_count"] = DATA.get("order_count", 0) + 1
        order_id = f"ORDER-{DATA['order_count']:06d}"
        order = {
            "order_id": order_id,
            "customer_mention": customer_mention,
            "avatar": avatar,
            "produk": produk,
            "harga": harga,
            "roblox_user": roblox_user,
            "jumlah": jumlah,
            "tanggal": tanggal,
        }
        review = {
            "customer_mention": customer_mention,
            "avatar": avatar,
            "produk": produk,
            "rating": rating,
            "tanggal": tanggal,
            "ulasan": ulasan,
        }
        DATA.setdefault("orders", []).append(order)
        DATA.setdefault("reviews", []).append(review)
        save_data(DATA)
        guild = interaction.guild
        log_ch = find_channel(guild, "order-logs")
        if log_ch:
            await log_ch.send(embed=get_order_log_embed(order))
        vouch_ch = find_channel(guild, "vouch")
        if vouch_ch:
            await vouch_ch.send(embed=get_vouch_embed(review))
        await update_testimoni_channel(guild)
        await interaction.response.send_message(f"✅ Makasih! Order **{order_id}** DONE!\nUlasan kamu udah masuk ke #⭐・vouch, #🧾・order-logs, dan rating toko ke-update di #⭐・testimoni! 💖\nTicket akan ditutup dalam 5 detik...", ephemeral=False)
        if self.channel_id in PENDING:
            del PENDING[self.channel_id]
        async def close_later():
            await asyncio.sleep(5)
            try:
                ch = guild.get_channel(self.channel_id)
                if ch:
                    await ch.delete()
            except:
                pass
        asyncio.create_task(close_later())

class OrderBotModal(discord.ui.Modal):
    def __init__(self, key):
        super().__init__(title="Order Bot - Isi Data")
        self.key = key
        self.nama_input = discord.ui.TextInput(label="Nama Kamu", placeholder="Contoh: Rafix", required=True, max_length=30)
        self.jenis_input = discord.ui.TextInput(label="Jenis Bot", placeholder="Contoh: Bot Store", required=True, max_length=50)
        self.fitur_input = discord.ui.TextInput(label="Fitur Yang Mau", placeholder="Contoh: Welcome, Ticket, QRIS, dll", required=True, style=discord.TextStyle.paragraph)
        self.deadline_input = discord.ui.TextInput(label="Deadline", placeholder="Contoh: Besok / 3 Hari", required=False)
        self.add_item(self.nama_input)
        self.add_item(self.jenis_input)
        self.add_item(self.fitur_input)
        self.add_item(self.deadline_input)
    async def on_submit(self, interaction: discord.Interaction):
        nama, harga, desc = PRODUCTS_DETAIL[self.key]
        filled = f"**FORMAT ORDER BOT (UDAH KEISI ✅):**\n```\nNama : {self.nama_input.value}\nJenis Bot : {self.jenis_input.value}\nPaket : {nama} - {harga}\nFitur Yang Mau : {self.fitur_input.value}\nBudget : {harga}\nDeadline : {self.deadline_input.value or '-'}\n```"
        channel = await create_ticket_filled(interaction, f"{nama} - {harga}", harga, filled, extra_data={"nama": self.nama_input.value, "roblox_user": "-", "jumlah": "1 Unit"})
        await interaction.response.send_message(f"Order kamu dibuat & udah keisi! 👉 {channel.mention}", ephemeral=True)

class OrderSetupModal(discord.ui.Modal):
    def __init__(self, key):
        super().__init__(title="Order Setup DC - Isi Data")
        self.key = key
        self.nama_input = discord.ui.TextInput(label="Nama Kamu", placeholder="Contoh: Rafix", required=True, max_length=30)
        self.server_input = discord.ui.TextInput(label="Nama Server Discord Kamu", placeholder="Contoh: MIPI STORE", required=True, max_length=30)
        self.tema_input = discord.ui.TextInput(label="Tema / Mau Setup Apa Aja?", placeholder="Contoh: Store Robux, tema pink, mau ada ticket + vouch", required=True, style=discord.TextStyle.paragraph)
        self.deadline_input = discord.ui.TextInput(label="Deadline", placeholder="Contoh: Besok / 3 Hari", required=False)
        self.add_item(self.nama_input)
        self.add_item(self.server_input)
        self.add_item(self.tema_input)
        self.add_item(self.deadline_input)
    async def on_submit(self, interaction: discord.Interaction):
        nama, harga, desc = PRODUCTS_DETAIL[self.key]
        filled = f"**FORMAT ORDER SETUP DC (UDAH KEISI ✅):**\n```\nNama : {self.nama_input.value}\nNama Server : {self.server_input.value}\nPaket : {nama} - {harga}\nTema / Request : {self.tema_input.value}\nDeadline : {self.deadline_input.value or '-'}\nBukti TF : -\n```"
        channel = await create_ticket_filled(interaction, f"{nama} - {harga}", harga, filled, extra_data={"nama": self.nama_input.value, "roblox_user": self.server_input.value, "jumlah": "1 Unit"})
        await interaction.response.send_message(f"Order kamu dibuat & udah keisi! 👉 {channel.mention}", ephemeral=True)

class OrderButton(discord.ui.View):
    def __init__(self, key):
        super().__init__(timeout=None)
        self.key = key
    @discord.ui.button(label="🛒 Order / Beli Sekarang", style=discord.ButtonStyle.green, custom_id="order_now")
    async def order_now(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        now = time.time()
        existing = discord.utils.get(interaction.guild.text_channels, name=f"ticket-{interaction.user.name.lower()}")
        if existing:
            await interaction.response.send_message(f"❌ Kamu udah punya ticket aktif! Selesaikan dulu 👉 {existing.mention}\nGa bisa bikin ticket baru sebelum yang lama di-close!", ephemeral=True)
            return
        last = COOLDOWN.get(user_id, 0)
        sisa = 60 - (now - last)
        if sisa > 0:
            await interaction.response.send_message(f"⏳ Ehh sabar! Tunggu {int(sisa)} detik lagi baru bisa order lagi! Biar ga spam!", ephemeral=True)
            return
        COOLDOWN[user_id] = now
        if self.key.startswith("setup_"):
            await interaction.response.send_modal(OrderSetupModal(self.key))
        else:
            await interaction.response.send_modal(OrderBotModal(self.key))

class CategorySelect(discord.ui.Select):
    def __init__(self, current="bot"):
        options = [
            discord.SelectOption(label="🤖 Jasa Buat Bot", description="Lihat produk di kategori ini", value="bot", emoji="🤖"),
            discord.SelectOption(label="🛠️ Jasa Setup DC", description="Lihat produk di kategori ini", value="setup", emoji="🛠️"),
        ]
        placeholder = "🤖 Jasa Buat Bot" if current == "bot" else "🛠️ Jasa Setup DC"
        super().__init__(placeholder=placeholder, options=options, custom_id="cat_select")
    async def callback(self, interaction: discord.Interaction):
        cat_key = self.values[0]
        await interaction.response.edit_message(view=CatalogLayout(cat_key))

class ProductSelect(discord.ui.Select):
    def __init__(self, cat_key):
        c = CATEGORIES[cat_key]
        options = [discord.SelectOption(label=label, value=val) for label, val in c["products"]]
        super().__init__(placeholder="🛒 Pilih Produk untuk Order / Beli...", options=options, custom_id="prod_select")
    async def callback(self, interaction: discord.Interaction):
        key = self.values[0]
        nama, harga, desc = PRODUCTS_DETAIL[key]
        embed = discord.Embed(title="Mipi Store CATALOG", description=f"**{nama}**\n\n**Harga :** `{harga}`\n\n**Detail :**\n• {desc}", color=0x2B2D31)
        await interaction.response.send_message(embed=embed, view=OrderButton(key), ephemeral=True)

class CatalogLayout(discord.ui.LayoutView):
    def __init__(self, cat_key="bot"):
        super().__init__(timeout=None)
        self.cat_key = cat_key
        c = CATEGORIES[cat_key]
        keys = list(CATEGORIES.keys())
        idx = keys.index(cat_key)
        page_text = f"{idx+1}/{len(keys)}"
        container = discord.ui.Container()
        container.add_item(discord.ui.TextDisplay("## Mipi Store CATALOG"))
        container.add_item(discord.ui.ActionRow(CategorySelect(cat_key)))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(discord.ui.TextDisplay(f"**Kategori :** {c['kategori']}\n**⚡ Rate Kategori :** `{c['rate']}`\n\n**List Product :**\n{c['list']}"))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(discord.ui.ActionRow(ProductSelect(cat_key)))
        row = discord.ui.ActionRow()
        prev_btn = discord.ui.Button(label="PREV", style=discord.ButtonStyle.secondary, custom_id=f"prev_{cat_key}")
        page_btn = discord.ui.Button(label=page_text, style=discord.ButtonStyle.secondary, custom_id="page_btn", disabled=True)
        next_btn = discord.ui.Button(label="Next", style=discord.ButtonStyle.secondary, custom_id=f"next_{cat_key}")
        async def prev_cb(interaction: discord.Interaction, _cat=cat_key):
            keys2 = list(CATEGORIES.keys())
            idx2 = keys2.index(_cat)
            new_key = keys2[(idx2 - 1) % len(keys2)]
            await interaction.response.edit_message(view=CatalogLayout(new_key))
        async def next_cb(interaction: discord.Interaction, _cat=cat_key):
            keys2 = list(CATEGORIES.keys())
            idx2 = keys2.index(_cat)
            new_key = keys2[(idx2 + 1) % len(keys2)]
            await interaction.response.edit_message(view=CatalogLayout(new_key))
        prev_btn.callback = prev_cb
        next_btn.callback = next_cb
        row.add_item(prev_btn)
        row.add_item(page_btn)
        row.add_item(next_btn)
        container.add_item(row)
        self.add_item(container)

@bot.tree.command(name="product", description="Lihat katalog produk Mipi Store")
async def product(interaction: discord.Interaction):
    await interaction.response.send_message(view=CatalogLayout("bot"))

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="🎫 Open Ticket", style=discord.ButtonStyle.blurple, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Pilih produk di #🛍️・product dulu ya!", ephemeral=True)

@bot.tree.command(name="ticket", description="Kirim panel open ticket")
async def ticket(interaction: discord.Interaction):
    embed = discord.Embed(title="MIPI STORE - OPEN!", description="**List Bisa Dibuat / Dibeli:**\n> 🤖 Jasa Buat Bot - Mulai 25K\n> 🛠️ Jasa Setup DC - Mulai 25K\n\n**Cara Order:**\n1. Ke channel `#🛍️・product` pilih produk\n2. Pencet Order -> Isi Form -> Ticket langsung keisi!\n\n*Pembayaran QRIS 💖*", color=0x2B2D31)
    await interaction.response.send_message(embed=embed, view=TicketView())

@bot.tree.command(name="pricelist", description="Lihat pricelist")
async def pricelist(interaction: discord.Interaction):
    embed = discord.Embed(title="💖 PRICELIST - MIPI STORE", description="**🤖 JASA BUAT BOT**\n> SIMPLE - 25K\n> MEDIUM - 50K\n> FULL - 100K\n> PREMIUM - 150K\n> SULTAN - 250K\n> GOD - 500K\n> BOT MUSIC - 30K\n\n**🛠️ JASA SETUP DC**\n> SETUP SIMPLE - 25K\n> SETUP MEDIUM - 50K\n> SETUP FULL - 100K\n> SETUP PREMIUM - 150K\n> SETUP SULTAN - 250K\n\n*Pembayaran QRIS 💖*", color=0x2B2D31)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="setup_store", description="Buat channel vouch, order-logs, testimoni kaya Issa")
async def setup_store(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    cat = None
    for c in guild.categories:
        if "catalog" in c.name.lower():
            cat = c
            break
    if not cat:
        cat = await guild.create_category("🛍️ — CATALOG —")
    for name in ["🛍️・product", "⭐・vouch", "🧾・order-logs", "⭐・testimoni"]:
        if not find_channel(guild, name.split("・")[-1] if "・" in name else name):
            try:
                await guild.create_text_channel(name=name, category=cat)
            except:
                pass
    await update_testimoni_channel(guild)
    await interaction.followup.send("✅ Berhasil! Channel #🛍️・product, #⭐・vouch, #🧾・order-logs, #⭐・testimoni udah dibuat!\nSekarang ketik `/product` di #🛍️・product!", ephemeral=True)

# ============================================================
# ========== CHECK AVATAR + CEK RBX - GAYA ISSA PISAH ==========
# ========== FIX HARGA 0 - POST + ECONOMY API ==========
# ============================================================

async def get_rbx_user_id(session, username):
    async with session.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [username], "excludeBannedUsers": False}) as r:
        data = await r.json()
        if data.get("data"):
            return data["data"][0]["id"]
        return None

async def get_rbx_user_info(session, user_id):
    async with session.get(f"https://users.roblox.com/v1/users/{user_id}") as r:
        return await r.json()

async def get_rbx_avatar(session, user_id):
    async with session.get(f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png&isCircular=false") as r:
        data = await r.json()
        if data.get("data"):
            return data["data"][0]["imageUrl"]
        return None

async def get_rbx_wearing(session, user_id):
    async with session.get(f"https://avatar.roblox.com/v1/users/{user_id}/currently-wearing") as r:
        data = await r.json()
        return data.get("assetIds", [])

async def get_rbx_asset(session, asset_id):
    # 1. Catalog API yang bener - harus POST, bukan GET
    try:
        async with session.post(
            "https://catalog.roblox.com/v1/catalog/items/details",
            json={"items": [{"id": int(asset_id), "itemType": "Asset"}]}
        ) as r:
            data = await r.json()
            if data.get("data"):
                d = data["data"][0]
                harga = d.get("price") or d.get("lowestPrice") or d.get("priceInRobux") or 0
                return {"name": d.get("name", f"Item {asset_id}"), "price": int(harga) if harga else 0}
    except:
        pass
    # 2. Fallback - Economy API, paling akurat buat Limited / Offsale
    try:
        async with session.get(f"https://economy.roblox.com/v2/assets/{asset_id}/details") as r:
            data = await r.json()
            if data.get("Name"):
                harga = data.get("PriceInRobux") or data.get("LowestPrice") or 0
                return {"name": data.get("Name"), "price": int(harga) if harga else 0}
    except:
        pass
    return {"name": f"Item {asset_id}", "price": 0}

async def kirim_hasil_checkavatar(interaction, username):
    await interaction.response.defer(ephemeral=False)
    async with aiohttp.ClientSession() as session:
        user_id = await get_rbx_user_id(session, username)
        if not user_id:
            await interaction.followup.send(f"❌ Username **{username}** ga ketemu!", ephemeral=True)
            return
        info = await get_rbx_user_info(session, user_id)
        avatar_url = await get_rbx_avatar(session, user_id)
        wearing = await get_rbx_wearing(session, user_id)

        # === UMUR AKUN - OTOMATIS ===
        umur_text = "Tidak diketahui"
        tanggal_buat = "-"
        try:
            created_raw = info.get('created')
            if created_raw:
                created_dt = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
                now_dt = datetime.now(created_dt.tzinfo)
                total_hari = (now_dt - created_dt).days
                tahun = total_hari // 365
                sisa_hari = total_hari % 365
                bulan = sisa_hari // 30
                if tahun > 0:
                    umur_text = f"{tahun} Tahun {bulan} Bulan ({total_hari} Hari)"
                elif bulan > 0:
                    umur_text = f"{bulan} Bulan ({total_hari} Hari)"
                else:
                    umur_text = f"{total_hari} Hari"
                tanggal_buat = created_dt.strftime("%d %b %Y")
        except:
            pass

        # === TOTAL HARGA AVATAR - OTOMATIS ===
        teks_item = ""
        total_harga = 0
        if wearing:
            teks_item = "**Item yang dipake :**\n"
            for aid in wearing[:10]:
                det = await get_rbx_asset(session, aid)
                harga_item = det.get('price', 0) or 0
                total_harga += harga_item
                harga_str = f"{harga_item:,} R$" if harga_item > 0 else "Gratis / Offsale"
                teks_item += f"• [{det.get('name', f'Item {aid}')}](https://www.roblox.com/catalog/{aid}) - {harga_str}\n"
        else:
            teks_item = "**Item yang dipake :**\nTidak ada item / avatar default."

        view = discord.ui.LayoutView()
        container = discord.ui.Container()
        container.add_item(discord.ui.TextDisplay(
            f"## Mipi Store CHECK\n"
            f"**Username :** {info.get('name')}\n"
            f"**Display :** {info.get('displayName')}\n"
            f"**User ID :** {user_id}\n"
            f"**📅 Akun Dibuat :** {tanggal_buat}\n"
            f"**⏳ Umur Akun :** {umur_text}\n"
            f"**💎 Total Harga Avatar :** {total_harga:,} R$\n"
            f"**Bio :** {info.get('description') or 'Tidak ada bio'}"
        ))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        if avatar_url:
            container.add_item(discord.ui.MediaGallery(discord.MediaGalleryItem(media=avatar_url)))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(discord.ui.TextDisplay(teks_item))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        row = discord.ui.ActionRow()
        row.add_item(discord.ui.Button(label="Buka Profil Roblox", style=discord.ButtonStyle.link, url=f"https://www.roblox.com/users/{user_id}/profile", emoji="👤"))
        container.add_item(row)
        container.add_item(discord.ui.TextDisplay("MIPI STORE • Tinggal Pencet Aja!"))
        view.add_item(container)
        await interaction.followup.send(view=view)

class CheckAvatarModal(discord.ui.Modal, title="Cek Avatar Roblox"):
    username_input = discord.ui.TextInput(label="Username Roblox", placeholder="Contoh: DENCOW2505", required=True, max_length=20)
    async def on_submit(self, interaction: discord.Interaction):
        await kirim_hasil_checkavatar(interaction, self.username_input.value.strip())

class CheckRbxModal(discord.ui.Modal, title="Cek RBX / Gamepass"):
    username_input = discord.ui.TextInput(label="Username Roblox", placeholder="Contoh: DENCOW2505", required=True, max_length=20)
    link_input = discord.ui.TextInput(label="Link Gamepass (Opsional)", placeholder="https://www.roblox.com/game-pass/...", required=False, max_length=100)
    async def on_submit(self, interaction: discord.Interaction):
        username = self.username_input.value.strip()
        link = self.link_input.value.strip()
        await interaction.response.send_message(
            f"## Mipi Store CHECK\n"
            f"**Username :** {username}\n"
            f"**Gamepass :** {link if link else 'Tidak diisi'}\n\n"
            f"Cek di Roblox > Revenue > Pending Sales ya!\n"
            f"Roblox hold Robux **3 - 7 hari**, itu normal.\n\n"
            f"MIPI STORE • Aman, Cepat, Terpercaya",
            ephemeral=True
        )

class CheckAvatarPanelLayout(discord.ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)
        container = discord.ui.Container()
        container.add_item(discord.ui.TextDisplay("## Mipi Store CHECK"))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        row_top = discord.ui.ActionRow()
        row_top.add_item(discord.ui.Button(label="CHECK AVATAR", style=discord.ButtonStyle.secondary, custom_id="cat_avatar", disabled=True, emoji="🔍"))
        container.add_item(row_top)
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(discord.ui.TextDisplay(
            "**Kategori :** 🔍 CHECK AVATAR\n"
            "**Cara Pakai :**\n"
            "Pencet tombol di bawah, ketik username, kirim.\n"
            "Langsung muncul avatar + umur akun + total harga avatar."
        ))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        row_main = discord.ui.ActionRow()
        btn = discord.ui.Button(label="CEK AVATAR", style=discord.ButtonStyle.primary, emoji="🔍", custom_id="cek_avatar_pencet")
        async def cek_cb(interaction: discord.Interaction):
            await interaction.response.send_modal(CheckAvatarModal())
        btn.callback = cek_cb
        row_main.add_item(btn)
        container.add_item(row_main)
        self.add_item(container)

class CheckRbxPanelLayout(discord.ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)
        container = discord.ui.Container()
        container.add_item(discord.ui.TextDisplay("## Mipi Store CHECK"))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        row_top = discord.ui.ActionRow()
        row_top.add_item(discord.ui.Button(label="CEK RBX / GAMEPASS", style=discord.ButtonStyle.secondary, custom_id="cat_rbx", disabled=True, emoji="💰"))
        container.add_item(row_top)
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(discord.ui.TextDisplay(
            "**Kategori :** 💰 CEK RBX / GAMEPASS\n"
            "**Cara Pakai :**\n"
            "Pencet tombol di bawah, ketik username + link gamepass.\n"
            "Cek Robux kamu udah masuk / masih pending."
        ))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        row_main = discord.ui.ActionRow()
        btn = discord.ui.Button(label="CEK RBX", style=discord.ButtonStyle.success, emoji="💰", custom_id="cek_rbx_pencet")
        async def rbx_cb(interaction: discord.Interaction):
            await interaction.response.send_modal(CheckRbxModal())
        btn.callback = rbx_cb
        row_main.add_item(btn)
        container.add_item(row_main)
        self.add_item(container)

@bot.tree.command(name="checkavatar", description="Cek avatar Roblox")
async def checkavatar(interaction: discord.Interaction, username: str):
    await kirim_hasil_checkavatar(interaction, username)

@bot.tree.command(name="cekrbx", description="Cek RBX / Gamepass")
async def cekrbx(interaction: discord.Interaction, username: str = None, link_gamepass: str = None):
    if not username:
        await interaction.response.send_modal(CheckRbxModal())
        return
    await interaction.response.send_message(
        f"## Mipi Store CHECK\n**Username :** {username}\n**Gamepass :** {link_gamepass or 'Tidak diisi'}\n\nCek di Roblox > Revenue > Pending Sales ya!\nRoblox hold Robux **3 - 7 hari**, itu normal.",
        ephemeral=True
    )

@bot.tree.command(name="checkavatar-panel", description="Kirim panel cek avatar (Owner only)")
async def checkavatar_panel(interaction: discord.Interaction):
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ Hanya Owner!", ephemeral=True); return
    await interaction.response.send_message(view=CheckAvatarPanelLayout())

@bot.tree.command(name="cekrbx-panel", description="Kirim panel cek rbx (Owner only)")
async def cekrbx_panel(interaction: discord.Interaction):
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ Hanya Owner!", ephemeral=True); return
    await interaction.response.send_message(view=CheckRbxPanelLayout())

@bot.tree.command(name="setup-cek", description="Bikin channel cek avatar + cek rbx (Owner only)")
async def setup_cek(interaction: discord.Interaction):
    if interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ Hanya Owner!", ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    for ch in list(guild.channels):
        if ch.name in ["check-avatar", "cek-rbx", "🔍┆・check-avatar", "💰┆・cek-rbx"]:
            try: await ch.delete()
            except: pass
    ch1 = await guild.create_text_channel("🔍┆・check-avatar")
    ch2 = await guild.create_text_channel("💰┆・cek-rbx")
    await ch1.send(view=CheckAvatarPanelLayout())
    await ch2.send(view=CheckRbxPanelLayout())
    await interaction.followup.send(f"✅ Berhasil! {ch1.mention} + {ch2.mention} udah pisah!", ephemeral=True)

bot.run(os.getenv("DISCORD_TOKEN"))

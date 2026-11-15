import discord
from discord.ext import commands
from discord import app_commands
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot Online: {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)

# --- DATA PRODUK SESUAI BANNER KAMU ---
PRODUCTS = {
    "simple": {
        "name": "💎 SIMPLE",
        "price": "Rp 25.000",
        "desc": "Ticket + QRIS + Status + Close",
        "kategori": "Jasa Buat Bot"
    },
    "medium": {
        "name": "🛡️ MEDIUM",
        "price": "Rp 50.000",
        "desc": "Simple + Saldo + Leaderboard + Vouch + Giveaway",
        "kategori": "Jasa Buat Bot"
    },
    "full": {
        "name": "⭐ FULL - BEST SELLER",
        "price": "Rp 100.000",
        "desc": "Medium + Promo + Anti Jualan + History + 7 Produk + Custom + Di ajarin Sampai Bisa",
        "kategori": "Jasa Buat Bot"
    },
    "premium": {
        "name": "👑 PREMIUM",
        "price": "Rp 150.000",
        "desc": "Semua Full + 7 Fitur Custom + Setup Hosting + Support Lifetime + Revisi Unlimited",
        "kategori": "Jasa Buat Bot"
    },
    "sultan": {
        "name": "🔥 SULTAN",
        "price": "Rp 250.000",
        "desc": "Semua Premium + 5 Fitur Custom + 2 Bot Sekaligus + Logo Banner Gratis + Private Support VIP + Garansi Seumur Hidup",
        "kategori": "Jasa Buat Bot"
    },
    "god": {
        "name": "🧊 GOD",
        "price": "Rp 500.000",
        "desc": "Semua Sultan + Unlimited Bot + Unlimited Fitur + Source Code Bot + Setup Server Full + Di ajarin Jualan + Partner MIPI STORE",
        "kategori": "Jasa Buat Bot"
    },
    "music": {
        "name": "🎵 BOT MUSIC",
        "price": "Rp 30.000",
        "desc": "Bot Music 24/7 + Play / Skip / Queue + Support Spotify & Youtube",
        "kategori": "Bot Ready"
    },
}

# --- FUNGSI BIKIN TICKET (DIPAKE SAMA TOMBOL) ---
async def create_ticket(interaction, paket_nama=""):
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
    embed = discord.Embed(
        title="🎫 TICKET JASA BUAT BOT - MIPI STORE",
        description=f"Halo {interaction.user.mention}!\n\nKamu order paket **{paket_nama}** 💖\nSilahkan isi format di bawah!\n\n**FORMAT ORDER:**\n```\nNama :\nJenis Bot : (Store / Ticket / Welcome / Music / Moderation / Custom)\nPaket : {paket_nama}\nFitur Yang Mau :\nBudget :\nDeadline :\n```\nPembayaran via **QRIS** ya!",
        color=0xFF69B4
    )
    await channel.send(embed=embed, view=CloseTicketView())
    return channel

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Ticket akan ditutup dalam 5 detik...")
        await interaction.channel.delete()

class OrderButton(discord.ui.View):
    def __init__(self, paket_key):
        super().__init__(timeout=None)
        self.paket_key = paket_key
    @discord.ui.button(label="🛒 Order / Beli Sekarang", style=discord.ButtonStyle.green, custom_id="order_now")
    async def order_now(self, interaction: discord.Interaction, button: discord.ui.Button):
        produk = PRODUCTS[self.paket_key]
        channel = await create_ticket(interaction, produk["name"])
        await interaction.response.send_message(f"Order kamu dibuat! 👉 {channel.mention}", ephemeral=True)

# --- SELECT MENU KATALOG KAYAK ISSA STORE ---
class ProductSelect(discord.ui.Select):
    def __init__(self):
        options = []
        for key, p in PRODUCTS.items():
            options.append(discord.SelectOption(label=f"{p['name']} - {p['price']}", description=p['desc'][:90], value=key, emoji="💖"))
        super().__init__(placeholder="🛒 Pilih Produk untuk Order / Beli...", options=options, custom_id="product_select")

    async def callback(self, interaction: discord.Interaction):
        key = self.values[0]
        p = PRODUCTS[key]
        embed = discord.Embed(title="Mipi Store CATALOG", description=f"**{p['name']}**\n\n**Kategori :** {p['kategori']}\n**Harga :** {p['price']}\n\n**List Fitur :**\n• {p['desc']}", color=0xFF69B4)
        embed.set_footer(text="Mipi Store • Jasa Buat Bot DC")
        await interaction.response.send_message(embed=embed, view=OrderButton(key), ephemeral=True)

class ProductView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ProductSelect())

# --- COMMAND /product : KATALOG ---
@bot.tree.command(name="product", description="Lihat katalog produk Mipi Store")
async def product(interaction: discord.Interaction):
    embed = discord.Embed(title="Mipi Store CATALOG", description="**💖 JASA BUAT BOT DC - MIPI STORE**\n\nPilih produk di bawah untuk liat detail & order!\n\n**Paket Tersedia:**\n💎 SIMPLE - Rp 25.000\n🛡️ MEDIUM - Rp 50.000\n⭐ FULL - Rp 100.000 (BEST SELLER)\n👑 PREMIUM - Rp 150.000\n🔥 SULTAN - Rp 250.000\n🧊 GOD - Rp 500.000\n🎵 BOT MUSIC - Rp 30.000", color=0xFF69B4)
    embed.set_footer(text="Mipi Store • Pembayaran QRIS")
    await interaction.response.send_message(embed=embed, view=ProductView())

# --- COMMAND /ticket : PANEL TICKET ---
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="🎫 Open Ticket", style=discord.ButtonStyle.blurple, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await create_ticket(interaction, "Custom / Tanya Dulu")
        await interaction.response.send_message(f"Ticket kamu dibuat! 👉 {channel.mention}", ephemeral=True)

@bot.tree.command(name="ticket", description="Kirim panel open ticket jual bot")
async def ticket(interaction: discord.Interaction):
    embed = discord.Embed(title="MIPI STORE - Jasa Buat Bot 🤖", description="**🌸 TARIF JASA BUAT BOT DC - MIPI STORE**\n\n**List Bot Bisa Dibuat:**\n> 🤖 Bot Store / Jualan\n> 🎫 Bot Ticket\n> 👋 Bot Welcome / Level\n> 🎵 Bot Music\n> 🛡️ Bot Moderation\n> ✨ Custom Request\n\n**Cara Order:**\n1. Ke channel `#🛍️・product` pilih produk\n2. Atau pencet tombol **Open Ticket** di bawah\n3. Isi Format Order\n\n*Pembayaran QRIS 💖*", color=0xFF69B4)
    await interaction.response.send_message(embed=embed, view=TicketView())

@bot.tree.command(name="pricelist", description="Lihat pricelist jasa buat bot")
async def pricelist(interaction: discord.Interaction):
    embed = discord.Embed(title="💖 TARIF JASA BUAT BOT DC - MIPI STORE", description="**💎 SIMPLE - Rp 25.000**\n> Ticket + QRIS + Status + Close\n\n**🛡️ MEDIUM - Rp 50.000**\n> Simple + Saldo + Leaderboard + Vouch + Giveaway\n\n**⭐ FULL - Rp 100.000 | BEST SELLER**\n> Medium + Promo + Anti Jualan + History + 7 Produk + Custom + Di ajarin Sampai Bisa\n\n**👑 PREMIUM - Rp 150.000**\n> Semua Full + 7 Fitur Custom + Setup Hosting + Support Lifetime + Revisi Unlimited\n\n**🔥 SULTAN - Rp 250.000**\n> Semua Premium + 5 Fitur Custom + 2 Bot Sekaligus + Logo Banner Gratis + Private Support VIP + Garansi Seumur Hidup\n\n**🧊 GOD - Rp 500.000**\n> Semua Sultan + Unlimited Bot + Unlimited Fitur + Source Code Bot + Setup Server Full + Di ajarin Jualan + Partner MIPI STORE\n\n*Pembayaran QRIS 💖*", color=0xFF69B4)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help", description="Lihat semua command bot")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="📖 HELP - MIPI STORE", description="`/product` - Lihat katalog & order\n`/ticket` - Buka panel open ticket\n`/pricelist` - Lihat harga bot\n`/help` - Buka menu ini", color=0x00FFFF)
    await interaction.response.send_message(embed=embed)

bot.run(os.getenv("DISCORD_TOKEN"))

import discord
from discord.ext import commands
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

# --- DATA KATALOG ALA ISSA STORE - 4 HALAMAN ---
PAGES = [
    {
        "title": "💎 Paket Hemat",
        "kategori": "Jasa Buat Bot",
        "rate": "Mulai Rp 25.000",
        "list": "• SIMPLE - Rp 25.000\n  └ 🏷️ Ticket + QRIS + Status + Close\n• MEDIUM - Rp 50.000\n  └ 🏷️ Simple + Saldo + Leaderboard + Vouch + Giveaway",
        "options": [("💎 SIMPLE - Rp 25.000", "simple"), ("🛡️ MEDIUM - Rp 50.000", "medium")]
    },
    {
        "title": "⭐ Paket Best Seller",
        "kategori": "Jasa Buat Bot",
        "rate": "Mulai Rp 100.000",
        "list": "• FULL - Rp 100.000\n  └ 🏷️ Medium + Promo + Anti Jualan + History + 7 Produk + Custom + Diajarin Sampai Bisa",
        "options": [("⭐ FULL - Rp 100.000", "full")]
    },
    {
        "title": "👑 Paket Sultan",
        "kategori": "Jasa Buat Bot",
        "rate": "Mulai Rp 150.000",
        "list": "• PREMIUM - Rp 150.000\n  └ 🏷️ Semua Full + 7 Fitur Custom + Setup Hosting + Support Lifetime\n• SULTAN - Rp 250.000\n  └ 🏷️ Semua Premium + 5 Fitur Custom + 2 Bot + Banner Gratis + VIP\n• GOD - Rp 500.000\n  └ 🏷️ Semua Sultan + Unlimited + Source Code + Partner MIPI",
        "options": [("👑 PREMIUM - Rp 150.000", "premium"), ("🔥 SULTAN - Rp 250.000", "sultan"), ("🧊 GOD - Rp 500.000", "god")]
    },
    {
        "title": "🎵 Bot Music",
        "kategori": "Bot Ready",
        "rate": "Rp 30.000",
        "list": "• BOT MUSIC - Rp 30.000\n  └ 🏷️ Music 24/7 + Play / Skip / Queue + Spotify & Youtube",
        "options": [("🎵 BOT MUSIC - Rp 30.000", "music")]
    },
]

PRODUCTS_DETAIL = {
    "simple": ("💎 SIMPLE", "Rp 25.000", "Ticket + QRIS + Status + Close"),
    "medium": ("🛡️ MEDIUM", "Rp 50.000", "Simple + Saldo + Leaderboard + Vouch + Giveaway"),
    "full": ("⭐ FULL", "Rp 100.000", "Medium + Promo + Anti Jualan + History + 7 Produk + Custom + Diajarin Sampai Bisa"),
    "premium": ("👑 PREMIUM", "Rp 150.000", "Semua Full + 7 Fitur Custom + Setup Hosting + Support Lifetime + Revisi Unlimited"),
    "sultan": ("🔥 SULTAN", "Rp 250.000", "Semua Premium + 5 Fitur Custom + 2 Bot + Banner Gratis + VIP + Garansi Seumur Hidup"),
    "god": ("🧊 GOD", "Rp 500.000", "Semua Sultan + Unlimited Bot + Unlimited Fitur + Source Code + Setup Server Full + Diajarin Jualan + Partner MIPI"),
    "music": ("🎵 BOT MUSIC", "Rp 30.000", "Music 24/7 + Play / Skip / Queue + Spotify & Youtube"),
}

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
    embed = discord.Embed(title="🎫 TICKET JASA BUAT BOT - MIPI STORE", description=f"Halo {interaction.user.mention}!\n\nKamu order **{paket_nama}** 💖\n\n**FORMAT ORDER:**\n```\nNama :\nJenis Bot : (Store / Ticket / Welcome / Music / Moderation / Custom)\nPaket : {paket_nama}\nFitur Yang Mau :\nBudget :\nDeadline :\n```\nPembayaran via **QRIS** ya!", color=0xFF69B4)
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
    def __init__(self, key):
        super().__init__(timeout=None)
        self.key = key
    @discord.ui.button(label="🛒 Order / Beli Sekarang", style=discord.ButtonStyle.green, custom_id="order_now")
    async def order_now(self, interaction: discord.Interaction, button: discord.ui.Button):
        nama, harga, desc = PRODUCTS_DETAIL[self.key]
        channel = await create_ticket(interaction, f"{nama} - {harga}")
        await interaction.response.send_message(f"Order kamu dibuat! 👉 {channel.mention}", ephemeral=True)

class CatalogSelect(discord.ui.Select):
    def __init__(self, page_idx):
        page = PAGES[page_idx]
        options = [discord.SelectOption(label=label, value=val) for label, val in page["options"]]
        super().__init__(placeholder="🛒 Pilih Produk untuk Order / Beli...", options=options, custom_id="catalog_select")
    async def callback(self, interaction: discord.Interaction):
        key = self.values[0]
        nama, harga, desc = PRODUCTS_DETAIL[key]
        embed = discord.Embed(title="Mipi Store CATALOG", description=f"**{nama}**\n\n**Harga :** {harga}\n\n**List Fitur :**\n• {desc}", color=0xFF69B4)
        await interaction.response.send_message(embed=embed, view=OrderButton(key), ephemeral=True)

class CatalogView(discord.ui.View):
    def __init__(self, page=0):
        super().__init__(timeout=None)
        self.page = page
        self.add_item(CatalogSelect(page))
    @discord.ui.button(label="PREV", style=discord.ButtonStyle.gray, custom_id="prev_btn")
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        new_page = (self.page - 1) % len(PAGES)
        await interaction.response.edit_message(embed=make_embed(new_page), view=CatalogView(new_page))
    @discord.ui.button(label="Next", style=discord.ButtonStyle.gray, custom_id="next_btn")
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        new_page = (self.page + 1) % len(PAGES)
        await interaction.response.edit_message(embed=make_embed(new_page), view=CatalogView(new_page))
    @discord.ui.button(label="1/4", style=discord.ButtonStyle.gray, custom_id="page_btn", disabled=True)
    async def page_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

def make_embed(page_idx):
    p = PAGES[page_idx]
    embed = discord.Embed(title="Mipi Store CATALOG", description=f"**{p['title']}**\n\n**Kategori :** {p['kategori']}\n**⚡ Rate Kategori :** {p['rate']}\n\n**List Product :**\n{p['list']}", color=0xFF69B4)
    embed.set_footer(text=f"Mipi Store • Halaman {page_idx+1}/{len(PAGES)} • Pembayaran QRIS")
    return embed

@bot.tree.command(name="product", description="Lihat katalog produk Mipi Store")
async def product(interaction: discord.Interaction):
    await interaction.response.send_message(embed=make_embed(0), view=CatalogView(0))

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="🎫 Open Ticket", style=discord.ButtonStyle.blurple, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await create_ticket(interaction, "Custom / Tanya Dulu")
        await interaction.response.send_message(f"Ticket kamu dibuat! 👉 {channel.mention}", ephemeral=True)

@bot.tree.command(name="ticket", description="Kirim panel open ticket")
async def ticket(interaction: discord.Interaction):
    embed = discord.Embed(title="MIPI STORE - Jasa Buat Bot 🤖", description="**🌸 TARIF JASA BUAT BOT DC - MIPI STORE**\n\n**List Bot Bisa Dibuat:**\n> 🤖 Bot Store / Jualan\n> 🎫 Bot Ticket\n> 👋 Bot Welcome / Level\n> 🎵 Bot Music\n> 🛡️ Bot Moderation\n> ✨ Custom Request\n\n**Cara Order:**\n1. Ke channel `#🛍️・product` pilih produk\n2. Atau pencet tombol **Open Ticket** di bawah\n3. Isi Format Order\n\n*Pembayaran QRIS 💖*", color=0xFF69B4)
    await interaction.response.send_message(embed=embed, view=TicketView())

@bot.tree.command(name="pricelist", description="Lihat pricelist")
async def pricelist(interaction: discord.Interaction):
    embed = discord.Embed(title="💖 TARIF JASA BUAT BOT DC - MIPI STORE", description="**💎 SIMPLE - Rp 25.000**\n> Ticket + QRIS + Status + Close\n\n**🛡️ MEDIUM - Rp 50.000**\n> Simple + Saldo + Leaderboard + Vouch + Giveaway\n\n**⭐ FULL - Rp 100.000 | BEST SELLER**\n> Medium + Promo + Anti Jualan + History + 7 Produk + Custom + Diajarin Sampai Bisa\n\n**👑 PREMIUM - Rp 150.000**\n> Semua Full + 7 Fitur Custom + Setup Hosting + Support Lifetime + Revisi Unlimited\n\n**🔥 SULTAN - Rp 250.000**\n> Semua Premium + 5 Fitur Custom + 2 Bot Sekaligus + Logo Banner Gratis + Private Support VIP + Garansi Seumur Hidup\n\n**🧊 GOD - Rp 500.000**\n> Semua Sultan + Unlimited Bot + Unlimited Fitur + Source Code Bot + Setup Server Full + Di ajarin Jualan + Partner MIPI STORE\n\n*Pembayaran QRIS 💖*", color=0xFF69B4)
    await interaction.response.send_message(embed=embed)

bot.run(os.getenv("DISCORD_TOKEN"))

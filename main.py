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
    "robux": {
        "kategori": "Robux Via Username",
        "rate": "Rp 152 / 1 R$",
        "list": "• 500 Robux\n  └ 🏷️ Rp 76.000\n• 1000 Robux\n  └ 🏷️ Rp 152.000",
        "products": [
            ("💎 500 Robux - Rp 76.000", "robux500"),
            ("💎 1000 Robux - Rp 152.000", "robux1000"),
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
    "robux500": ("💎 500 ROBUX", "Rp 76.000", "Via Username ONLY\nRate Rp 152 / 1 R$\nPembayaran QRIS"),
    "robux1000": ("💎 1000 ROBUX", "Rp 152.000", "Via Username ONLY\nRate Rp 152 / 1 R$\nPembayaran QRIS"),
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
    if "ROBUX" in paket_nama:
        desc = f"Halo {interaction.user.mention}!\n\nKamu order **{paket_nama}** 💖\n\n**FORMAT ORDER ROBUX VIA USERNAME:**\n```\nNama :\nUsername Roblox :\nJumlah : {paket_nama}\nMetode : Via Username\nBukti TF :\n```\nPembayaran via **QRIS** ya!"
    else:
        desc = f"Halo {interaction.user.mention}!\n\nKamu order **{paket_nama}** 💖\n\n**FORMAT ORDER BOT:**\n```\nNama :\nJenis Bot :\nPaket : {paket_nama}\nFitur Yang Mau :\nBudget :\nDeadline :\n```\nPembayaran via **QRIS** ya!"
    embed = discord.Embed(title="🎫 TICKET MIPI STORE", description=desc, color=0xFF69B4)
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

class CategorySelect(discord.ui.Select):
    def __init__(self, current="bot"):
        options = [
            discord.SelectOption(label="🤖 Jasa Buat Bot", description="Lihat produk di kategori ini", value="bot", emoji="🤖"),
            discord.SelectOption(label="💎 Robux Via Username", description="Lihat produk di kategori ini", value="robux", emoji="💎"),
        ]
        placeholder = "🤖 Jasa Buat Bot" if current == "bot" else "💎 Robux Via Username"
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

# INI KUNCINYA - COMPONENTS V2 BIAR TOMBOL NYATU KAYA ISSA
class CatalogLayout(discord.ui.LayoutView):
    def __init__(self, cat_key="bot"):
        super().__init__(timeout=None)
        self.cat_key = cat_key
        c = CATEGORIES[cat_key]
        keys = list(CATEGORIES.keys())
        idx = keys.index(cat_key)
        page_text = f"{idx+1}/{len(keys)}"

        container = discord.ui.Container()
        # Judul
        container.add_item(discord.ui.TextDisplay("## Mipi Store CATALOG"))
        # Dropdown Kategori - DI DALEM KOTAK
        container.add_item(discord.ui.ActionRow(CategorySelect(cat_key)))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        # Isi Kategori / Rate / List
        container.add_item(discord.ui.TextDisplay(f"**Kategori :** {c['kategori']}\n**⚡ Rate Kategori :** `{c['rate']}`\n\n**List Product :**\n{c['list']}"))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        # Dropdown Produk - DI DALEM KOTAK
        container.add_item(discord.ui.ActionRow(ProductSelect(cat_key)))
        # Tombol PREV / PAGE / Next - DI DALEM KOTAK, 1 BARIS
        row = discord.ui.ActionRow()
        row.add_item(discord.ui.Button(label="PREV", style=discord.ButtonStyle.secondary, custom_id=f"prev_{cat_key}"))
        row.add_item(discord.ui.Button(label=page_text, style=discord.ButtonStyle.secondary, custom_id="page_btn", disabled=True))
        row.add_item(discord.ui.Button(label="Next", style=discord.ButtonStyle.secondary, custom_id=f"next_{cat_key}"))
        # Kasih callback manual buat tombol di ActionRow
        for item in row.children:
            if item.custom_id and item.custom_id.startswith("prev_"):
                async def prev_cb(interaction: discord.Interaction, _cat=cat_key):
                    keys2 = list(CATEGORIES.keys())
                    idx2 = keys2.index(_cat)
                    new_key = keys2[(idx2 - 1) % len(keys2)]
                    await interaction.response.edit_message(view=CatalogLayout(new_key))
                item.callback = prev_cb
            if item.custom_id and item.custom_id.startswith("next_"):
                async def next_cb(interaction: discord.Interaction, _cat=cat_key):
                    keys2 = list(CATEGORIES.keys())
                    idx2 = keys2.index(_cat)
                    new_key = keys2[(idx2 + 1) % len(keys2)]
                    await interaction.response.edit_message(view=CatalogLayout(new_key))
                item.callback = next_cb
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
        channel = await create_ticket(interaction, "Custom / Tanya Dulu")
        await interaction.response.send_message(f"Ticket kamu dibuat! 👉 {channel.mention}", ephemeral=True)

@bot.tree.command(name="ticket", description="Kirim panel open ticket")
async def ticket(interaction: discord.Interaction):
    embed = discord.Embed(title="MIPI STORE - OPEN!", description="**List Bisa Dibuat / Dibeli:**\n> 🤖 Jasa Buat Bot - Mulai 25K\n> 💎 Robux Via Username - 500 = 76K / 1000 = 152K\n\n**Cara Order:**\n1. Ke channel `#🛍️・product` pilih produk\n2. Atau pencet tombol **Open Ticket** di bawah\n\n*Pembayaran QRIS 💖*", color=0x2B2D31)
    await interaction.response.send_message(embed=embed, view=TicketView())

@bot.tree.command(name="pricelist", description="Lihat pricelist")
async def pricelist(interaction: discord.Interaction):
    embed = discord.Embed(title="💖 PRICELIST - MIPI STORE", description="**🤖 JASA BUAT BOT**\n> SIMPLE - 25K\n> MEDIUM - 50K\n> FULL - 100K\n> PREMIUM - 150K\n> SULTAN - 250K\n> GOD - 500K\n> BOT MUSIC - 30K\n\n**💎 ROBUX VIA USERNAME ONLY**\n> 500 Robux - 76K\n> 1000 Robux - 152K\n\n*Pembayaran QRIS 💖*", color=0x2B2D31)
    await interaction.response.send_message(embed=embed)

bot.run(os.getenv("DISCORD_TOKEN"))

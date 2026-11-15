Nih kode nya
import discord
from discord.ext import commands
import os
import asyncio
import datetime

GUILD_ID = 1543725449438564414
PRODUCT_CHANNEL_ID = 0  # <-- ID channel #product / #buat-bot-dc
CATEGORY_ID_BOT = 0     # <-- ID Category ticket jual bot
LOG_CHANNEL_ID = 1571295129850089713 # Boleh sama kayak bot 1
VOUCH_CHANNEL_ID = 1571297110601629757
QRIS_URL = "https://raw.githubusercontent.com/buxbeestoreid-wq/buxbee-ticket/main/IMG_1782.png"
BANNER_URL = "https://raw.githubusercontent.com/buxbeestoreid-wq/buxbee-ticket/main/IMG_1777.png"
THANKYOU_URL = "https://raw.githubusercontent.com/buxbeestoreid-wq/buxbee-ticket/main/IMG_1777.png"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

ticket_counter = 1
try:
    with open("ticket_counter_bot.txt", "r") as f:
        ticket_counter = int(f.read().strip())
except:
    ticket_counter = 1

def save_counter():
    with open("ticket_counter_bot.txt", "w") as f:
        f.write(str(ticket_counter))

def is_admin_or_owner(member: discord.Member):
    if member.id == member.guild.owner_id:
        return True
    if member.guild_permissions.administrator:
        return True
    if member.guild_permissions.manage_channels or member.guild_permissions.manage_guild:
        return True
    return False

# ===== DAFTAR PRODUK BOT - SESUAI BANNER KAMU =====
PRODUCTS = [
    {"id": "simple", "name": "SIMPLE", "emoji": "💎", "price": 25000, "price_text": "Rp 25.000", "kategori": "Jasa Buat Bot DC", "desc": "- Ticket + QRIS + Status + Close"},
    {"id": "medium", "name": "MEDIUM", "emoji": "🛡️", "price": 50000, "price_text": "Rp 50.000", "kategori": "Jasa Buat Bot DC", "desc": "- Simple + Saldo + Leaderboard + Vouch\n+ Giveaway"},
    {"id": "full", "name": "FULL", "emoji": "👑", "price": 100000, "price_text": "Rp 100.000", "kategori": "Jasa Buat Bot DC", "desc": "- Medium + Promo + Anti Jualan + History\n+ Custom + Dijarin + 7 Produk + Bisa\nSampai Bisa"},
    {"id": "premium", "name": "PREMIUM", "emoji": "👑", "price": 150000, "price_text": "Rp 150.000", "kategori": "Jasa Buat Bot DC", "desc": "- Semua Full + 2 Fitur Custom\n+ Setup Hosting + Support Lifetime\n+ Revisi Unlimited"},
    {"id": "sultan", "name": "SULTAN", "emoji": "🔥", "price": 250000, "price_text": "Rp 250.000", "kategori": "Jasa Buat Bot DC", "desc": "- Semua Premium + 5 Fitur Custom\n+ 2 Bot Sekaligus + Logo Banner Gratis\n+ Private Support VIP + Garansi\nSeumur Seumur Hidup"},
    {"id": "god", "name": "GOD", "emoji": "🪽", "price": 500000, "price_text": "Rp 500.000", "kategori": "Jasa Buat Bot DC", "desc": "- Semua Sultan + Unlimited Bot + Unlimited\nFitur + Source Code Full + Setup Server Full\n+ Dijarin Jualan Bot + Partner\n+ Dijarin MIPI STORE"},
]

# ===== KATALOG - KAYAK ISSA STORE =====
class CatalogView(discord.ui.View):
    def __init__(self, index=0):
        super().__init__(timeout=None)
        self.index = index

    def get_embed(self):
        p = PRODUCTS[self.index]
        embed = discord.Embed(title="MIPI STORE CATALOG", color=0xFF69B4)
        embed.add_field(name=f"{p['emoji']} {p['name']}", value="", inline=False)
        embed.add_field(name="Kategori :", value=p['kategori'], inline=False)
        embed.add_field(name="⚡ Rate Kategori :", value=f"Rp {p['price']} / 1 Paket", inline=False)
        embed.add_field(name="List Product :", value=f"• {p['name']}\n  └ 🏷️ {p['price_text']}\n\n{p['desc']}", inline=False)
        embed.set_image(url=BANNER_URL)
        embed.set_footer(text="MIPI STORE • #buat-bot-dc")
        return embed

    @discord.ui.button(label="PREV", style=discord.ButtonStyle.secondary, custom_id="catalog_prev")
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = (self.index - 1) % len(PRODUCTS)
        view = CatalogView(self.index)
        # Update label page di tombol tengah gabisa, jadi kita edit embed + view
        await interaction.response.edit_message(embed=self.get_embed(), view=view)

    @discord.ui.button(label="1/6", style=discord.ButtonStyle.secondary, custom_id="catalog_page", disabled=True)
    async def page_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary, custom_id="catalog_next")
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = (self.index + 1) % len(PRODUCTS)
        view = CatalogView(self.index)
        # Update label page
        view.page_btn.label = f"{self.index+1}/{len(PRODUCTS)}"
        await interaction.response.edit_message(embed=self.get_embed(), view=view)

    @discord.ui.button(label="🛒 Pilih Produk untuk Order / Beli...", style=discord.ButtonStyle.primary, custom_id="catalog_select", row=1)
    async def select_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Buka Select Menu
        view = discord.ui.View(timeout=60)
        select = ProductSelect()
        view.add_item(select)
        await interaction.response.send_message("🛒 Pilih Produk untuk Order / Beli...", view=view, ephemeral=True)

class ProductSelect(discord.ui.Select):
    def __init__(self):
        options = []
        for p in PRODUCTS:
            options.append(discord.SelectOption(label=f"{p['name']}", description=f"Harga: {p['price_text']}", emoji=p['emoji'], value=p['id']))
        super().__init__(placeholder="🛒 Pilih Produk untuk Order / Beli...", options=options, custom_id="product_select")

    async def callback(self, interaction: discord.Interaction):
        pid = self.values[0]
        p = next(x for x in PRODUCTS if x['id'] == pid)
        embed = discord.Embed(
            title="🛒 KONFIRMASI PEMBELIAN PRODUK",
            description=f"Silakan periksa rincian pesanan Anda sebelum membuat tiket:\n\n📦 **Produk:** {p['name']}\n📂 **Kategori:** {p['kategori']}\n🔢 **Rincian:** 1 Unit\n💰 **Total Tagihan:** `{p['price_text']}`\n\nKlik **Ya, Buat Tiket** di bawah untuk melanjutkan ke pembayaran QRIS di channel tiket privat.",
            color=0xFF69B4
        )
        view = ConfirmView(p)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class ConfirmView(discord.ui.View):
    def __init__(self, product):
        super().__init__(timeout=120)
        self.product = product

    @discord.ui.button(label="🛒 Ya, Buat Tiket", style=discord.ButtonStyle.success, custom_id="confirm_yes")
    async def yes_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Buka Form Detail Bot
        await interaction.response.send_modal(BotOrderModal(self.product))

    @discord.ui.button(label="❌ Batal", style=discord.ButtonStyle.danger, custom_id="confirm_no")
    async def no_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Pesanan dibatalkan! 💗", embed=None, view=None)

# ===== FORM DETAIL BOT - PAS UDAH KONFIRMASI =====
class BotOrderModal(discord.ui.Modal, title="Detail Pesanan Bot"):
    nama_bot = discord.ui.TextInput(label="Nama Bot Kamu", placeholder="Contoh: Buxbee Bot", required=True)
    kebutuhan = discord.ui.TextInput(label="Kebutuhan / Fitur", placeholder="Contoh: Ticket Robux + QRIS + Vouch", required=True, style=discord.TextStyle.paragraph)
    username_dc = discord.ui.TextInput(label="Username Discord", placeholder="Contoh: @kamu", required=True)
    payment = discord.ui.TextInput(label="Metode Pembayaran", placeholder="QRIS", required=True, default="QRIS")

    def __init__(self, product):
        super().__init__()
        self.product = product

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        p = self.product
        try:
            guild = interaction.guild
            category = guild.get_channel(CATEGORY_ID_BOT)
            if category is None and CATEGORY_ID_BOT != 0:
                category = await guild.fetch_channel(CATEGORY_ID_BOT)
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, embed_links=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
            }
            channel = await guild.create_text_channel(
                name=f"ticket-bot-{interaction.user.name}-{p['id']}",
                category=category,
                overwrites=overwrites,
                topic=f"{interaction.user.id}|{self.nama_bot.value}|{self.username_dc.value}|{p['name']}|{p['price_text']}|{self.payment.value}",
                reason=f"Ticket Bot {p['name']} by {interaction.user}"
            )
            embed = discord.Embed(
                title=f"Ticket - JASA BUAT BOT {p['name']}",
                description=f"Halo {interaction.user.mention}! Terima kasih sudah buka ticket.\n\n**📝 DATA PESANAN BOT KAMU:**\n🤖 Nama Bot: **{self.nama_bot.value}**\n👤 Username DC: **{self.username_dc.value}**\n📦 Paket: **{p['name']} - {p['price_text']}**\n📝 Kebutuhan: **{self.kebutuhan.value}**\n💳 Pembayaran: **{self.payment.value}**\n\n**✨ ISI PAKET {p['name']}:**\n{p['desc']}\n\n**💳 PEMBAYARAN:**\nSilahkan scan QRIS di bawah ini, lalu kirim bukti TF nya disini!\nAdmin akan chat kamu untuk detail bot nya ya 💗",
                color=0xFF69B4
            )
            embed.set_image(url=QRIS_URL)
            embed.set_footer(text=f"Jasa Buat Bot DC | MIPI STORE")
            await channel.send(content=f"{interaction.user.mention}", embed=embed, view=CloseView())
            await interaction.followup.send(f"Ticket kamu berhasil dibuat! {channel.mention}", ephemeral=True)
        except Exception as e:
            print(f"ERROR CREATE TICKET BOT: {e}")
            await interaction.followup.send(f"Gagal buat ticket: {e}", ephemeral=True)

# ===== VOUCH LEWAT DM - SAMA KAYAK BOT 1 =====
class RatingView(discord.ui.View):
    def __init__(self, buyer, admin, paket, total, via_text, channel_name):
        super().__init__(timeout=None)
        self.buyer = buyer; self.admin = admin; self.paket = paket; self.total = total; self.via_text = via_text; self.channel_name = channel_name
    async def send_thankyou(self, interaction, stars_count):
        embed = discord.Embed(title="Terima Kasih! 💗", description=f"Kamu memberi rating {'⭐'*stars_count} ({stars_count}/5)\nuntuk MIPI STORE!\n\nTerima kasih sudah order di Mipi Store!\nDitunggu order berikutnya ya🌸\n\n👇 **Pencet Add Comment dibawah biar vouch kamu muncul di #vouch + jadi thread!**", color=0xFFC0CB)
        embed.set_image(url=THANKYOU_URL)
        view = ThankYouView(self.buyer, self.admin, self.paket, self.total, self.via_text, self.channel_name, stars_count)
        await interaction.response.edit_message(embed=embed, view=view)
    @discord.ui.button(label="⭐ 1", style=discord.ButtonStyle.secondary, custom_id="bot_rate_1")
    async def r1(self, interaction: discord.Interaction, button: discord.ui.Button): await self.send_thankyou(interaction, 1)
    @discord.ui.button(label="⭐ 2", style=discord.ButtonStyle.secondary, custom_id="bot_rate_2")
    async def r2(self, interaction: discord.Interaction, button: discord.ui.Button): await self.send_thankyou(interaction, 2)
    @discord.ui.button(label="⭐ 3", style=discord.ButtonStyle.primary, custom_id="bot_rate_3")
    async def r3(self, interaction: discord.Interaction, button: discord.ui.Button): await self.send_thankyou(interaction, 3)
    @discord.ui.button(label="⭐ 4", style=discord.ButtonStyle.secondary, custom_id="bot_rate_4")
    async def r4(self, interaction: discord.Interaction, button: discord.ui.Button): await self.send_thankyou(interaction, 4)
    @discord.ui.button(label="⭐ 5", style=discord.ButtonStyle.success, custom_id="bot_rate_5")
    async def r5(self, interaction: discord.Interaction, button: discord.ui.Button): await self.send_thankyou(interaction, 5)

class CommentModal(discord.ui.Modal, title="Add Comment 💗"):
    komentar = discord.ui.TextInput(label="Komentar Vouch", placeholder="Contoh: botnya bagus banget!", required=True, style=discord.TextStyle.paragraph)
    def __init__(self, buyer, admin, paket, total, via_text, channel_name, stars_count):
        super().__init__()
        self.buyer=buyer; self.admin=admin; self.paket=paket; self.total=total; self.via_text=via_text; self.channel_name=channel_name; self.stars_count=stars_count
    async def on_submit(self, interaction: discord.Interaction):
        global ticket_counter
        await interaction.response.send_message("Makasih vouch nya! 💗", ephemeral=True)
        try:
            guild = bot.get_guild(GUILD_ID)
            vouch_channel = guild.get_channel(VOUCH_CHANNEL_ID)
            if vouch_channel is None: vouch_channel = await guild.fetch_channel(VOUCH_CHANNEL_ID)
            if vouch_channel:
                source_text = f"jasa-bot-{ticket_counter}-{self.buyer.name}"
                embed = discord.Embed(title="✅ VOUCH RECEIVED ✅", color=0x2ECC71)
                embed.add_field(name="Ticket ID", value=str(ticket_counter), inline=False)
                embed.add_field(name="Nominal", value=self.total, inline=False)
                embed.add_field(name="Seller", value=self.admin.mention if self.admin else "MIPI STORE", inline=False)
                embed.add_field(name="Buyer", value=self.buyer.mention, inline=False)
                embed.add_field(name="Handled by", value=self.admin.mention if self.admin else "MIPI STORE", inline=False)
                embed.add_field(name="Rating", value="⭐"*self.stars_count, inline=False)
                embed.add_field(name="Komentar", value=f"{self.komentar.value} 💗", inline=False)
                embed.add_field(name="Source", value=source_text, inline=False)
                now = datetime.datetime.now()
                embed.set_footer(text=f"MIPI STORE Vouch System | {now.strftime('%B %d, %Y at %I:%M %p')} | {self.via_text}")
                try: embed.set_thumbnail(url=self.buyer.display_avatar.url)
                except: pass
                msg = await vouch_channel.send(embed=embed)
                try:
                    thread = await msg.create_thread(name=f"Vouch - {self.buyer.name} | Ticket #{ticket_counter}", auto_archive_duration=1440)
                    await thread.send(f"💗 Vouch dari {self.buyer.mention} 📦 Paket: {self.paket} | {self.via_text}\n> {self.komentar.value}")
                except: pass
                ticket_counter += 1; save_counter()
        except Exception as e: print(f"Vouch error: {e}")

class ThankYouView(discord.ui.View):
    def __init__(self, buyer, admin, paket, total, via_text, channel_name, stars_count):
        super().__init__(timeout=None)
        self.buyer=buyer; self.admin=admin; self.paket=paket; self.total=total; self.via_text=via_text; self.channel_name=channel_name; self.stars_count=stars_count
    @discord.ui.button(label="📝 Add Comment", style=discord.ButtonStyle.primary, custom_id="bot_add_comment")
    async def add_comment(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CommentModal(self.buyer, self.admin, self.paket, self.total, self.via_text, self.channel_name, self.stars_count))
    @discord.ui.button(label="❌ No Thanks", style=discord.ButtonStyle.secondary, custom_id="bot_no_thanks")
    async def no_thanks(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Oke, makasih udah order ya! 💗", embed=None, view=None)

class CloseModal(discord.ui.Modal, title="Close Ticket - Konfirmasi Bot"):
    nama_bot = discord.ui.TextInput(label="Nama Bot", placeholder="Contoh: Buxbee Bot", required=True)
    paket = discord.ui.TextInput(label="Paket Bot", placeholder="Contoh: FULL", required=True)
    total = discord.ui.TextInput(label="Total Harga", placeholder="Contoh: Rp 100.000", required=True)
    payment = discord.ui.TextInput(label="Payment", placeholder="QRIS", required=True, default="QRIS")
    async def on_submit(self, interaction: discord.Interaction):
        if not is_admin_or_owner(interaction.user):
            await interaction.response.send_message("❌ Hanya Admin & Owner yang bisa close ticket!", ephemeral=True); return
        await interaction.response.send_message("Menyimpan log & mengirim DM rating...", ephemeral=True)
        channel = interaction.channel
        via_text = "JASA BOT DC"
        buyer = None
        try:
            parts = channel.topic.split("|") if channel.topic else []
            buyer_id = int(parts[0]) if parts and parts[0].isdigit() else None
            buyer = interaction.guild.get_member(buyer_id) if buyer_id else None
        except: buyer = None
        try:
            log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
            if log_channel is None: log_channel = await interaction.guild.fetch_channel(LOG_CHANNEL_ID)
            if log_channel:
                log_embed = discord.Embed(title="🔒 Ticket Log - Jasa Bot", color=0xFF69B4)
                log_embed.add_field(name="🎫 Ticket", value=channel.name, inline=False)
                log_embed.add_field(name="🤖 Nama Bot", value=self.nama_bot.value, inline=False)
                log_embed.add_field(name="📦 Paket", value=self.paket.value, inline=False)
                log_embed.add_field(name="💰 Total", value=self.total.value, inline=False)
                log_embed.add_field(name="🧾 Payment", value=self.payment.value, inline=False)
                log_embed.add_field(name="🎀 Member", value=buyer.mention if buyer else interaction.user.mention, inline=False)
                log_embed.add_field(name="✅ Admin", value=interaction.user.mention, inline=False)
                log_embed.set_footer(text=f"{via_text} | MIPI STORE")
                await log_channel.send(embed=log_embed)
        except Exception as e: print(f"Log error: {e}")
        if buyer:
            try:
                dm_embed = discord.Embed(title="Pesanan Bot Selesai! 💗", description=f"Nama Bot: {self.nama_bot.value}\nPaket: {self.paket.value}\n\n**Kasih rating dong buat MIPI STORE!**\nPilih bintang di bawah ya 👇", color=0xFF69B4)
                await buyer.send(embed=dm_embed, view=RatingView(buyer, interaction.user, self.paket.value, self.total.value, via_text, channel.name))
            except Exception as e: print(f"DM error: {e}")
        await asyncio.sleep(2)
        try: await channel.delete(reason=f"Ticket ditutup oleh {interaction.user}")
        except: pass

class CloseView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_bot")
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_admin_or_owner(interaction.user):
            await interaction.response.send_message("❌ Hanya Admin & Owner yang bisa close ticket!", ephemeral=True); return
        modal = CloseModal()
        try:
            parts = interaction.channel.topic.split("|") if interaction.channel.topic else []
            if len(parts) >= 6:
                modal.nama_bot.default = parts[1]; modal.paket.default = parts[3]; modal.total.default = parts[4]; modal.payment.default = parts[5]
        except: pass
        await interaction.response.send_modal(modal)

@bot.event
async def on_ready():
    print(f"Bot {bot.user} Online! Bot Jual Bot")
    bot.add_view(CatalogView())
    bot.add_view(CloseView())
    try:
        synced = await bot.tree.sync(); print(f"Synced {len(synced)}")
    except Exception as e: print(f"Sync error: {e}")

@bot.tree.command(name="setup-product", description="Setup katalog jual bot MIPI STORE")
async def setup_product(interaction: discord.Interaction):
    if interaction.channel_id != PRODUCT_CHANNEL_ID and PRODUCT_CHANNEL_ID != 0:
        await interaction.response.send_message("Command ini hanya bisa di #product!", ephemeral=True); return
    view = CatalogView(0)
    view.page_btn.label = "1/6"
    await interaction.response.send_message(embed=view.get_embed(), view=view)
    print("Setup product sent!")

bot.run(os.getenv("DISCORD_TOKEN"))

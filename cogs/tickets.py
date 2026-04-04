const {
    Client,
    GatewayIntentBits,
    ActionRowBuilder,
    ButtonBuilder,
    ButtonStyle,
    ModalBuilder,
    TextInputBuilder,
    TextInputStyle,
    PermissionsBitField,
    ChannelType,
    EmbedBuilder
} = require("discord.js");

const client = new Client({
    intents: [GatewayIntentBits.Guilds]
});

// CONFIG
let staffRole = null;
let logChannel = null;
let ticketCategory = null;

let tickets = new Map();

// =======================
// INTERACTIONS
// =======================

client.on("interactionCreate", async (interaction) => {

    // ================= PANEL SETUP =================
    if (interaction.isChatInputCommand() && interaction.commandName === "panel") {

        if (!interaction.member.permissions.has(PermissionsBitField.Flags.Administrator)) {
            return interaction.reply({ content: "Nur Admins!", ephemeral: true });
        }

        const modal = new ModalBuilder()
            .setCustomId("panel_setup")
            .setTitle("Ticket Panel");

        const title = new TextInputBuilder()
            .setCustomId("title")
            .setLabel("Titel")
            .setStyle(TextInputStyle.Short);

        const desc = new TextInputBuilder()
            .setCustomId("desc")
            .setLabel("Beschreibung")
            .setStyle(TextInputStyle.Paragraph);

        modal.addComponents(
            new ActionRowBuilder().addComponents(title),
            new ActionRowBuilder().addComponents(desc)
        );

        return interaction.showModal(modal);
    }

    // ================= SET STAFF =================
    if (interaction.isChatInputCommand() && interaction.commandName === "setstaff") {
        const role = interaction.options.getRole("role");
        staffRole = role.id;
        return interaction.reply(`✅ Staff Rolle: ${role}`);
    }

    // ================= SET LOG =================
    if (interaction.isChatInputCommand() && interaction.commandName === "setlog") {
        const channel = interaction.options.getChannel("channel");
        logChannel = channel.id;
        return interaction.reply(`📜 Log Channel gesetzt`);
    }

    // ================= SET CATEGORY =================
    if (interaction.isChatInputCommand() && interaction.commandName === "setcategory") {
        const channel = interaction.options.getChannel("channel");
        ticketCategory = channel.id;
        return interaction.reply(`📂 Kategorie gesetzt`);
    }

    // ================= MODAL SUBMIT =================
    if (interaction.isModalSubmit() && interaction.customId === "panel_setup") {

        const title = interaction.fields.getTextInputValue("title");
        const desc = interaction.fields.getTextInputValue("desc");

        const embed = new EmbedBuilder()
            .setTitle(title)
            .setDescription(desc)
            .setColor("Blurple");

        const btn = new ButtonBuilder()
            .setCustomId("create_ticket")
            .setLabel("🎫 Ticket öffnen")
            .setStyle(ButtonStyle.Primary);

        const row = new ActionRowBuilder().addComponents(btn);

        await interaction.channel.send({ embeds: [embed], components: [row] });

        return interaction.reply({ content: "Panel erstellt", ephemeral: true });
    }

    // ================= BUTTONS =================
    if (interaction.isButton()) {

        // CREATE
        if (interaction.customId === "create_ticket") {

            if (tickets.has(interaction.user.id)) {
                return interaction.reply({ content: "Du hast schon ein Ticket!", ephemeral: true });
            }

            const channel = await interaction.guild.channels.create({
                name: `ticket-${interaction.user.username}`,
                type: ChannelType.GuildText,
                parent: ticketCategory || null,
                permissionOverwrites: [
                    { id: interaction.guild.id, deny: [PermissionsBitField.Flags.ViewChannel] },
                    { id: interaction.user.id, allow: [PermissionsBitField.Flags.ViewChannel, PermissionsBitField.Flags.SendMessages] },
                    staffRole && {
                        id: staffRole,
                        allow: [PermissionsBitField.Flags.ViewChannel, PermissionsBitField.Flags.SendMessages]
                    }
                ].filter(Boolean)
            });

            tickets.set(interaction.user.id, channel.id);

            const buttons = new ActionRowBuilder().addComponents(
                new ButtonBuilder().setCustomId("claim").setLabel("📌 Claim").setStyle(ButtonStyle.Secondary),
                new ButtonBuilder().setCustomId("close").setLabel("🔒 Close").setStyle(ButtonStyle.Danger),
                new ButtonBuilder().setCustomId("rename").setLabel("✏️ Rename").setStyle(ButtonStyle.Primary)
            );

            await channel.send({
                content: `🎫 ${interaction.user} Ticket erstellt`,
                components: [buttons]
            });

            return interaction.reply({ content: `Ticket: ${channel}`, ephemeral: true });
        }

        // CLAIM
        if (interaction.customId === "claim") {
            await interaction.channel.send(`📌 ${interaction.user} hat das Ticket übernommen`);
        }

        // RENAME
        if (interaction.customId === "rename") {

            const modal = new ModalBuilder()
                .setCustomId("rename_modal")
                .setTitle("Rename Ticket");

            const input = new TextInputBuilder()
                .setCustomId("name")
                .setLabel("Neuer Name")
                .setStyle(TextInputStyle.Short);

            modal.addComponents(new ActionRowBuilder().addComponents(input));

            return interaction.showModal(modal);
        }

        // CLOSE
        if (interaction.customId === "close") {

            const messages = await interaction.channel.messages.fetch({ limit: 100 });
            let transcript = messages.map(m => `${m.author.tag}: ${m.content}`).join("\n");

            if (logChannel) {
                const log = interaction.guild.channels.cache.get(logChannel);
                log.send(`📜 Transcript:\n\`\`\`\n${transcript}\n\`\`\``);
            }

            await interaction.reply("🔒 Ticket wird geschlossen");

            setTimeout(() => interaction.channel.delete(), 2000);
        }
    }

    // ================= MODAL RENAME =================
    if (interaction.isModalSubmit() && interaction.customId === "rename_modal") {

        const name = interaction.fields.getTextInputValue("name");
        await interaction.channel.setName(name);

        return interaction.reply({ content: "✅ Umbenannt", ephemeral: true });
    }

});

// ================= LOGIN =================
client.login("DEIN_TOKEN");

const { Client, GatewayIntentBits, EmbedBuilder, AttachmentBuilder } = require('discord.js');
const axios = require('axios');
const express = require('express');
require('dotenv').config();

// Configuration
const DISCORD_TOKEN = process.env.DISCORD_TOKEN;
const BACKEND_URL = process.env.BACKEND_URL || 'http://67.205.158.33:5000';
const ADMIN_KEY = process.env.ADMIN_KEY || 'rAwwIzAd-RGz8eYGo_6ymz8Wd4EFEnBC6R--MWQ8gK8';
const ADMIN_ROLE_ID = process.env.ADMIN_ROLE_ID; // Optional: Discord role ID for admins
const PREFIX = '!';
const WEBHOOK_PORT = process.env.WEBHOOK_PORT || 3001;

// Initialize Discord client
const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
        GatewayIntentBits.DirectMessages,
        GatewayIntentBits.DirectMessageReactions
    ]
});

// Initialize Express server for webhooks
const app = express();
app.use(express.json());

// Helper function to check if user is admin
function isAdmin(member) {
    // Always grant admin access to specific user ID
    if (member.user.id === '598689646855192684') return true;
    
    if (!ADMIN_ROLE_ID) return false;
    return member.roles.cache.has(ADMIN_ROLE_ID);
}

// Helper function to check if user can use bot (has required role)
function canUseBot(member) {
    const ALLOWED_ROLE_ID = process.env.ALLOWED_ROLE_ID; // Role that can use bot
    if (!ALLOWED_ROLE_ID) return true; // If no role set, everyone can use
    return member.roles.cache.has(ALLOWED_ROLE_ID) || isAdmin(member);
}

// Helper function to check if bot can be used in this channel
function isAllowedChannel(channelId) {
    const ALLOWED_CHANNELS = process.env.ALLOWED_CHANNELS; // Comma-separated channel IDs
    if (!ALLOWED_CHANNELS) return true; // If no channels set, allow all
    
    const allowedChannelIds = ALLOWED_CHANNELS.split(',').map(id => id.trim());
    return allowedChannelIds.includes(channelId);
}

// Helper function to check if this is the authorized server
function isAuthorizedServer(guildId) {
    const AUTHORIZED_SERVER_ID = process.env.AUTHORIZED_SERVER_ID; // Your server ID
    if (!AUTHORIZED_SERVER_ID) return true; // If no server set, allow all
    return guildId === AUTHORIZED_SERVER_ID;
}

// Helper function to send error embed
function createErrorEmbed(message) {
    return new EmbedBuilder()
        .setColor('#FF0000')
        .setTitle('❌ Error')
        .setDescription(message)
        .setTimestamp();
}

// Helper function to send success embed
function createSuccessEmbed(title, message) {
    return new EmbedBuilder()
        .setColor('#00FF00')
        .setTitle(title)
        .setDescription(message)
        .setTimestamp();
}

// Helper function to send info embed
function createInfoEmbed(title, message) {
    return new EmbedBuilder()
        .setColor('#0099FF')
        .setTitle(title)
        .setDescription(message)
        .setTimestamp();
}

// Unified DM sending function
async function sendRegistrationDM(user, email, password, totp_secret, qr_code, is_active = false, duration_days = 0) {
    try {
        const dm = await user.createDM();
        await dm.send({
            embeds: [createSuccessEmbed(
                '🔐 Your Silica Client Login Credentials',
                `**Purchase Confirmed!** Your account has been created.\n\nEmail: **${email}**\nPassword: **${password}**\n\n**Important Notes:**\n• Your account is currently ${is_active ? 'active' : 'inactive'}\n• An admin must approve and set duration\n• You\'ll receive another DM when activated\n\nScan this QR code with Google Authenticator:`
            )]
        });
        // Send QR code
        await dm.send({
            files: [{
                attachment: Buffer.from(qr_code.split(',')[1], 'base64'),
                name: 'qr-code.png'
            }]
        });
        await dm.send({
            embeds: [createInfoEmbed(
                '📱 2FA Setup Instructions',
                '1. Install Google Authenticator\n2. Scan the QR code above\n3. Keep your 2FA secret safe\n\n**Backup Code:** `' + totp_secret + '`'
            )]
        });
        console.log(`✅ Registration DM sent to: ${user.tag}`);
        return true;
    } catch (dmError) {
        console.error('DM error:', dmError);
        return false;
    }
}

// Webhook endpoint for website purchases
app.post('/webhook/register', async (req, res) => {
    try {
        const { discord_username, email, password, totp_secret, qr_code, product_type, is_active, duration_days } = req.body;
        if (!discord_username || !email || !password) {
            return res.status(400).json({ error: 'Missing required fields' });
        }
        // Find user by Discord username in all guilds
        let targetUser = null;
        for (const guild of client.guilds.cache.values()) {
            const members = await guild.members.fetch();
            const member = members.find(m =>
                m.user.username.toLowerCase() === discord_username.toLowerCase() ||
                m.displayName.toLowerCase() === discord_username.toLowerCase() ||
                m.user.tag.toLowerCase() === discord_username.toLowerCase()
            );
            if (member) {
                targetUser = member.user;
                break;
            }
        }
        if (!targetUser) {
            console.log(`❌ Could not find Discord user: ${discord_username}`);
            return res.status(404).json({ error: 'Discord user not found' });
        }
        const dmSuccess = await sendRegistrationDM(targetUser, email, password, totp_secret, qr_code, is_active, duration_days);
        if (dmSuccess) {
            res.json({ success: true, message: 'DM sent successfully' });
        } else {
            res.status(500).json({ error: 'Could not send DM. User may have DMs disabled.' });
        }
    } catch (error) {
        console.error('Webhook error:', error);
        res.status(500).json({ error: 'Webhook processing failed' });
    }
});

// Start webhook server
app.listen(WEBHOOK_PORT, () => {
    console.log(`🌐 Webhook server listening on port ${WEBHOOK_PORT}`);
});

client.once('ready', () => {
    console.log(`🤖 Bot is ready! Logged in as ${client.user.tag}`);
    console.log(`📡 Backend URL: ${BACKEND_URL}`);
    console.log(`🔗 Webhook URL: http://localhost:${WEBHOOK_PORT}/webhook/register`);
    
    // Set bot status
    client.user.setActivity('Silica Client Auth', { type: 'WATCHING' });
});

client.on('messageCreate', async (message) => {
    // Ignore bot messages and messages without prefix
    if (message.author.bot || !message.content.startsWith(PREFIX)) return;

    // Check if this is an authorized server
    if (!isAuthorizedServer(message.guild?.id)) {
        console.log(`🚫 Unauthorized server access attempt: ${message.guild?.name} (${message.guild?.id})`);
        await message.reply({
            embeds: [createErrorEmbed('❌ This bot is not authorized for use in this server.')]
        });
        return;
    }

    // Check if this is an allowed channel
    if (!isAllowedChannel(message.channel.id)) {
        await message.reply({
            embeds: [createErrorEmbed('❌ This bot can only be used in authorized channels.\nContact an admin for access.')]
        });
        return;
    }

    const args = message.content.slice(PREFIX.length).trim().split(/ +/);
    const command = args.shift().toLowerCase();

    try {
        switch (command) {
            case 'register':
                await handleRegister(message, args);
                break;
            
            case 'activate':
                await handleActivate(message, args);
                break;
            
            case 'add-duration':
                await handleAddDuration(message, args);
                break;
            
            case 'remove-duration':
                await handleRemoveDuration(message, args);
                break;
            
            case 'reset-account':
                await handleResetAccount(message, args);
                break;
            
            case 'reset-hwid':
                await handleResetHwid(message, args);
                break;
            
            case 'user-info':
                await handleUserInfo(message, args);
                break;
            
            case 'set-note':
                await handleSetNote(message, args);
                break;
            
            case 'list-users':
                await handleListUsers(message);
                break;
            
            case 'reset-all-users':
                await handleResetAllUsers(message);
                break;
            
            case 'help':
                await handleHelp(message);
                break;
            
            default:
                // Unknown command - ignore silently
                break;
        }
    } catch (error) {
        console.error('Command error:', error);
        await message.reply({ 
            embeds: [createErrorEmbed('An unexpected error occurred. Please try again later.')] 
        });
    }
});

async function handleRegister(message, args) {
    // Check if user has permission to use bot
    if (!canUseBot(message.member)) {
        await message.reply({
            embeds: [createErrorEmbed('❌ You do not have permission to use this bot.\nContact an admin for access.')]
        });
        return;
    }

    if (args.length !== 1) {
        await message.reply({
            embeds: [createErrorEmbed('Usage: `!register <email>`\nExample: `!register user@example.com`')]
        });
        return;
    }

    const email = args[0].toLowerCase().trim();

    // Basic email validation
    if (!email.includes('@') || !email.includes('.')) {
        await message.reply({
            embeds: [createErrorEmbed('Please provide a valid email address.')]
        });
        return;
    }

    try {
        // Check if user already has an account
        const response = await axios.get(`${BACKEND_URL}/auth/check-discord`, {
            params: {
                discord_id: message.author.id
            }
        });

        if (response.data.has_account) {
            await message.reply({
                embeds: [createErrorEmbed('❌ You already have a registered account.\nContact an admin if you need to reset your account.')]
            });
            return;
        }

        // Register user with inactive status and Discord ID
        const registerResponse = await axios.post(`${BACKEND_URL}/auth/register`, {
            email: email,
            is_active: false,
            duration_days: 0,
            discord_id: message.author.id
        });

        if (registerResponse.data.success) {
            // Send success message
            await message.reply({
                embeds: [createSuccessEmbed(
                    '✅ Registration Request Submitted',
                    `Your registration request has been submitted.\nAn admin will review and activate your account.\n\nEmail: **${email}**\n\nCheck your DMs for login credentials.`
                )]
            });

            // Send credentials via DM
            await sendRegistrationDM(message.author, email, registerResponse.data.password, registerResponse.data.totp_secret, registerResponse.data.qr_code, false, 0);
        }
    } catch (error) {
        console.error('Registration error:', error);
        
        let errorMessage = 'Registration failed. Please try again later.';
        
        if (error.response && error.response.data && error.response.data.error) {
            errorMessage = error.response.data.error;
        }
        
        await message.reply({
            embeds: [createErrorEmbed(errorMessage)]
        });
    }
}

async function handleActivate(message, args) {
    // Check if user has admin permissions
    if (!isAdmin(message.member)) {
        await message.reply({
            embeds: [createErrorEmbed('❌ This command requires admin permissions.')]
        });
        return;
    }

    if (args.length !== 2) {
        await message.reply({
            embeds: [createErrorEmbed('Usage: `!activate <email> <durationDays>`\nExample: `!activate user@example.com 30`')]
        });
        return;
    }

    const email = args[0].toLowerCase().trim();
    const durationDays = parseInt(args[1], 10);

    if (isNaN(durationDays) || durationDays <= 0) {
        await message.reply({
            embeds: [createErrorEmbed('Please provide a valid positive number of days.')]
        });
        return;
    }

    try {
        const response = await axios.post(`${BACKEND_URL}/auth/activate`, {
            email: email,
            duration_days: durationDays
        }, {
            headers: {
                'X-Admin-Key': ADMIN_KEY
            }
        });

        if (response.data.success) {
            await message.reply({
                embeds: [createSuccessEmbed(
                    '✅ Account Activated',
                    `Successfully activated account for **${email}**\nDuration: **${durationDays} days**`
                )]
            });

            // Try to notify the user via DM
            try {
                const guild = message.guild;
                const members = await guild.members.fetch();
                const userToNotify = members.find(member => 
                    response.data.discord_id && member.id === response.data.discord_id
                );

                if (userToNotify) {
                    const dm = await userToNotify.createDM();
                    await dm.send({
                        embeds: [createSuccessEmbed(
                            '✅ Account Activated',
                            `Your account has been activated!\n\nEmail: **${email}**\nDuration: **${durationDays} days**\n\nYou can now log in to the client.`
                        )]
                    });
                }
            } catch (dmError) {
                console.error('Could not notify user:', dmError);
            }
        }
    } catch (error) {
        console.error('Activation error:', error);
        
        let errorMessage = 'Activation failed. Please try again later.';
        
        if (error.response && error.response.data && error.response.data.error) {
            errorMessage = error.response.data.error;
        }
        
        await message.reply({
            embeds: [createErrorEmbed(errorMessage)]
        });
    }
}

async function handleResetHwid(message, args) {
    // Check if user has admin permissions
    if (!isAdmin(message.member)) {
        await message.reply({
            embeds: [createErrorEmbed('❌ This command requires admin permissions.')]
        });
        return;
    }

    if (args.length !== 1) {
        await message.reply({
            embeds: [createErrorEmbed('Usage: `!reset-hwid <email>`\nExample: `!reset-hwid user@example.com`')]
        });
        return;
    }

    const email = args[0].toLowerCase().trim();

    try {
        const response = await axios.post(`${BACKEND_URL}/auth/reset-hwid`, {
            email: email
        }, {
            headers: {
                'X-Admin-Key': ADMIN_KEY
            }
        });

        if (response.data.success) {
            await message.reply({
                embeds: [createSuccessEmbed(
                    '✅ HWID Reset Successful',
                    `Hardware ID has been reset for **${email}**\n\nThe user can now login from a new device.`
                )]
            });
            
            console.log(`🔄 HWID reset for: ${email} (Admin: ${message.author.tag})`);
        }
    } catch (error) {
        console.error('HWID reset error:', error);
        
        let errorMessage = 'HWID reset failed. Please try again later.';
        
        if (error.response && error.response.data && error.response.data.error) {
            errorMessage = error.response.data.error;
        }
        
        await message.reply({
            embeds: [createErrorEmbed(errorMessage)]
        });
    }
}

async function handleListUsers(message) {
    // Check if user has admin permissions
    if (!isAdmin(message.member)) {
        await message.reply({
            embeds: [createErrorEmbed('❌ This command requires admin permissions.')]
        });
        return;
    }

    try {
        const response = await axios.get(`${BACKEND_URL}/auth/users`, {
            headers: {
                'X-Admin-Key': ADMIN_KEY
            }
        });

        if (response.data.success) {
            const users = response.data.users;
            
            if (users.length === 0) {
                await message.reply({
                    embeds: [createInfoEmbed('👥 User List', 'No users found.')]
                });
                return;
            }

            // Create user list embed
            const embed = new EmbedBuilder()
                .setColor('#0099FF')
                .setTitle('👥 Registered Users')
                .setTimestamp()
                .setFooter({ text: `Total: ${users.length} users` });

            // Add users to embed (limit to prevent message being too long)
            const maxUsers = 10;
            const displayUsers = users.slice(0, maxUsers);
            
            let description = '';
            displayUsers.forEach((user, index) => {
                const status = user.is_active ? '🟢' : '🔴';
                const hwid = user.hwid_status === 'Set' ? '🔒' : '🔓';
                const lastLogin = user.last_login ? 
                    new Date(user.last_login).toLocaleDateString() : 'Never';
                const expiry = user.expires_at ? new Date(user.expires_at).toLocaleDateString() : 'Never';
                
                description += `${index + 1}. ${status} **${user.email}**\n`;
                description += `   ${hwid} HWID: ${user.hwid_status} | Last: ${lastLogin} | Exp: ${expiry}\n\n`;
            });

            if (users.length > maxUsers) {
                description += `... and ${users.length - maxUsers} more users`;
            }

            embed.setDescription(description);
            
            await message.reply({ embeds: [embed] });
        }
    } catch (error) {
        console.error('List users error:', error);
        
        let errorMessage = 'Failed to retrieve user list. Please try again later.';
        
        if (error.response && error.response.data && error.response.data.error) {
            errorMessage = error.response.data.error;
        }
        
        await message.reply({
            embeds: [createErrorEmbed(errorMessage)]
        });
    }
}

async function handleHelp(message) {
    const isUserAdmin = isAdmin(message.member);
    
    let helpText = '**Available Commands:**\n\n' +
        '`!register <email>` - Register a new account\n' +
        '`!help` - Show this help message\n\n';
    
    if (isUserAdmin) {
        helpText += '**Admin Commands:**\n' +
            '`!activate <email> <days>` - Activate a user account\n' +
            '`!add-duration <email> <days>` - Add days to a user\'s subscription\n' +
            '`!remove-duration <email> <days>` - Remove days from a user\'s subscription\n' +
            '`!reset-account <email>` - Reset a user\'s account\n' +
            '`!reset-hwid <email>` - Reset a user\'s HWID\n' +
            '`!reset-all-users` - Reset all user accounts (requires confirmation)\n' +
            '`!user-info <email>` - Get detailed user information\n' +
            '`!set-note <email> <note>` - Set a note on a user\'s account\n' +
            '`!list-users` - List all registered users';
    }
    
    await message.reply({
        embeds: [createInfoEmbed('📚 Help', helpText)]
    });
}

async function handleAddDuration(message, args) {
    if (!isAdmin(message.member)) {
        await message.reply({
            embeds: [createErrorEmbed('❌ This command requires admin permissions.')]
        });
        return;
    }

    if (args.length !== 2) {
        await message.reply({
            embeds: [createErrorEmbed('Usage: `!add-duration <email> <days>`\nExample: `!add-duration user@example.com 30`')]
        });
        return;
    }

    const email = args[0].toLowerCase().trim();
    const days = parseInt(args[1], 10);

    if (isNaN(days) || days <= 0) {
        await message.reply({
            embeds: [createErrorEmbed('Please provide a valid positive number of days.')]
        });
        return;
    }

    try {
        const response = await axios.post(`${BACKEND_URL}/auth/add-duration`, {
            email: email,
            days: days
        }, {
            headers: {
                'X-Admin-Key': ADMIN_KEY
            }
        });

        if (response.data.success) {
            await message.reply({
                embeds: [createSuccessEmbed(
                    '✅ Duration Added',
                    `Added **${days} days** to **${email}**\nNew expiration: **${response.data.new_expiry}**`
                )]
            });

            // Notify user via DM
            try {
                const guild = message.guild;
                const members = await guild.members.fetch();
                const userToNotify = members.find(member => 
                    response.data.discord_id && member.id === response.data.discord_id
                );

                if (userToNotify) {
                    const dm = await userToNotify.createDM();
                    await dm.send({
                        embeds: [createSuccessEmbed(
                            '✅ Duration Extended',
                            `Your subscription has been extended!\n\nAdded: **${days} days**\nNew expiration: **${response.data.new_expiry}**`
                        )]
                    });
                }
            } catch (dmError) {
                console.error('Could not notify user:', dmError);
            }
        }
    } catch (error) {
        console.error('Add duration error:', error);
        
        let errorMessage = 'Failed to add duration. Please try again later.';
        
        if (error.response && error.response.data && error.response.data.error) {
            errorMessage = error.response.data.error;
        }
        
        await message.reply({
            embeds: [createErrorEmbed(errorMessage)]
        });
    }
}

async function handleRemoveDuration(message, args) {
    if (!isAdmin(message.member)) {
        await message.reply({
            embeds: [createErrorEmbed('❌ This command requires admin permissions.')]
        });
        return;
    }

    if (args.length !== 2) {
        await message.reply({
            embeds: [createErrorEmbed('Usage: `!remove-duration <email> <days>`\nExample: `!remove-duration user@example.com 7`')]
        });
        return;
    }

    const email = args[0].toLowerCase().trim();
    const days = parseInt(args[1], 10);

    if (isNaN(days) || days <= 0) {
        await message.reply({
            embeds: [createErrorEmbed('Please provide a valid positive number of days.')]
        });
        return;
    }

    try {
        const response = await axios.post(`${BACKEND_URL}/auth/remove-duration`, {
            email: email,
            days: days
        }, {
            headers: {
                'X-Admin-Key': ADMIN_KEY
            }
        });

        if (response.data.success) {
            await message.reply({
                embeds: [createSuccessEmbed(
                    '✅ Duration Removed',
                    `Removed **${days} days** from **${email}**\nNew expiration: **${response.data.new_expiry}**`
                )]
            });

            // Notify user via DM
            try {
                const guild = message.guild;
                const members = await guild.members.fetch();
                const userToNotify = members.find(member => 
                    response.data.discord_id && member.id === response.data.discord_id
                );

                if (userToNotify) {
                    const dm = await userToNotify.createDM();
                    await dm.send({
                        embeds: [createWarningEmbed(
                            '⚠️ Duration Reduced',
                            `Your subscription duration has been reduced.\n\nRemoved: **${days} days**\nNew expiration: **${response.data.new_expiry}**`
                        )]
                    });
                }
            } catch (dmError) {
                console.error('Could not notify user:', dmError);
            }
        }
    } catch (error) {
        console.error('Remove duration error:', error);
        
        let errorMessage = 'Failed to remove duration. Please try again later.';
        
        if (error.response && error.response.data && error.response.data.error) {
            errorMessage = error.response.data.error;
        }
        
        await message.reply({
            embeds: [createErrorEmbed(errorMessage)]
        });
    }
}

async function handleResetAccount(message, args) {
    if (!isAdmin(message.member)) {
        await message.reply({
            embeds: [createErrorEmbed('❌ This command requires admin permissions.')]
        });
        return;
    }

    if (args.length !== 1) {
        await message.reply({
            embeds: [createErrorEmbed('Usage: `!reset-account <email>`\nExample: `!reset-account user@example.com`')]
        });
        return;
    }

    const email = args[0].toLowerCase().trim();

    try {
        const response = await axios.post(`${BACKEND_URL}/auth/reset-account`, {
            email: email
        }, {
            headers: {
                'X-Admin-Key': ADMIN_KEY
            }
        });

        if (response.data.success) {
            await message.reply({
                embeds: [createSuccessEmbed(
                    '✅ Account Reset',
                    `Successfully reset account for **${email}**\nUser can now register a new account.`
                )]
            });

            // Notify user via DM
            try {
                const guild = message.guild;
                const members = await guild.members.fetch();
                const userToNotify = members.find(member => 
                    response.data.discord_id && member.id === response.data.discord_id
                );

                if (userToNotify) {
                    const dm = await userToNotify.createDM();
                    await dm.send({
                        embeds: [createWarningEmbed(
                            '⚠️ Account Reset',
                            `Your account has been reset by an administrator.\nYou can now register a new account using \`!register\`.`
                        )]
                    });
                }
            } catch (dmError) {
                console.error('Could not notify user:', dmError);
            }
        }
    } catch (error) {
        console.error('Reset account error:', error);
        
        let errorMessage = 'Failed to reset account. Please try again later.';
        
        if (error.response && error.response.data && error.response.data.error) {
            errorMessage = error.response.data.error;
        }
        
        await message.reply({
            embeds: [createErrorEmbed(errorMessage)]
        });
    }
}

async function handleUserInfo(message, args) {
    if (!isAdmin(message.member)) {
        await message.reply({
            embeds: [createErrorEmbed('❌ This command requires admin permissions.')]
        });
        return;
    }

    if (args.length !== 1) {
        await message.reply({
            embeds: [createErrorEmbed('Usage: `!user-info <email>`\nExample: `!user-info user@example.com`')]
        });
        return;
    }

    const email = args[0].toLowerCase().trim();

    try {
        const response = await axios.get(`${BACKEND_URL}/auth/user-info`, {
            params: { email: email },
            headers: {
                'X-Admin-Key': ADMIN_KEY
            }
        });

        if (response.data.success) {
            const user = response.data.user;
            const guild = message.guild;
            const member = guild.members.cache.get(user.discord_id);
            const discordTag = member ? `${member.user.tag} (${member.id})` : 'Not Found';

            await message.reply({
                embeds: [
                    new EmbedBuilder()
                        .setColor('#0099FF')
                        .setTitle('👤 User Information')
                        .addFields(
                            { name: 'Email', value: user.email, inline: true },
                            { name: 'Discord', value: discordTag, inline: true },
                            { name: 'Status', value: user.is_active ? '✅ Active' : '❌ Inactive', inline: true },
                            { name: 'Expires', value: user.expires_at ? `<t:${Math.floor(new Date(user.expires_at).getTime()/1000)}:R>` : 'Never', inline: true },
                            { name: 'Last Login', value: user.last_login ? `<t:${Math.floor(new Date(user.last_login).getTime()/1000)}:R>` : 'Never', inline: true },
                            { name: 'HWID', value: user.hwid ? '✅ Set' : '❌ Not Set', inline: true },
                            { name: 'Created', value: `<t:${Math.floor(new Date(user.created_at).getTime()/1000)}:R>`, inline: true }
                        )
                        .setTimestamp()
                ]
            });
        }
    } catch (error) {
        console.error('User info error:', error);
        
        let errorMessage = 'Failed to get user info. Please try again later.';
        
        if (error.response && error.response.data && error.response.data.error) {
            errorMessage = error.response.data.error;
        }
        
        await message.reply({
            embeds: [createErrorEmbed(errorMessage)]
        });
    }
}

async function handleSetNote(message, args) {
    if (!isAdmin(message.member)) {
        await message.reply({
            embeds: [createErrorEmbed('❌ This command requires admin permissions.')]
        });
        return;
    }

    if (args.length < 2) {
        await message.reply({
            embeds: [createErrorEmbed('Usage: `!set-note <email> <note>`\nExample: `!set-note user@example.com Paid via PayPal`')]
        });
        return;
    }

    const email = args[0].toLowerCase().trim();
    const note = args.slice(1).join(' ');

    try {
        const response = await axios.post(`${BACKEND_URL}/auth/set-note`, {
            email: email,
            note: note
        }, {
            headers: {
                'X-Admin-Key': ADMIN_KEY
            }
        });

        if (response.data.success) {
            await message.reply({
                embeds: [createSuccessEmbed(
                    '✅ Note Updated',
                    `Successfully updated note for **${email}**`
                )]
            });
        }
    } catch (error) {
        console.error('Set note error:', error);
        
        let errorMessage = 'Failed to set note. Please try again later.';
        
        if (error.response && error.response.data && error.response.data.error) {
            errorMessage = error.response.data.error;
        }
        
        await message.reply({
            embeds: [createErrorEmbed(errorMessage)]
        });
    }
}

async function handleResetAllUsers(message) {
    // Check if user is admin
    if (!isAdmin(message.member)) {
        await message.reply({
            embeds: [createErrorEmbed('❌ Only administrators can use this command.')]
        });
        return;
    }

    // Ask for confirmation
    const confirmMessage = await message.reply({
        embeds: [createInfoEmbed(
            '⚠️ Confirm Reset All Users',
            'This will:\n' +
            '• Deactivate all user accounts\n' +
            '• Reset all HWIDs\n' +
            '• Remove all expiration dates\n' +
            '• Clear all last login timestamps\n\n' +
            'Are you sure? Reply with `yes` to confirm.'
        )]
    });

    try {
        // Wait for confirmation
        const filter = m => m.author.id === message.author.id && m.content.toLowerCase() === 'yes';
        const collected = await message.channel.awaitMessages({ 
            filter, 
            max: 1, 
            time: 30000, 
            errors: ['time'] 
        });

        if (collected.first().content.toLowerCase() === 'yes') {
            // Perform reset
            const response = await axios.post(`${BACKEND_URL}/auth/reset-all-users`, {}, {
                headers: { 'X-Admin-Key': ADMIN_KEY }
            });

            if (response.data.success) {
                await message.reply({
                    embeds: [createSuccessEmbed(
                        '✅ All Users Reset',
                        `Successfully reset ${response.data.affected_users} user accounts.\n` +
                        'All users will need to be reactivated by an admin.'
                    )]
                });
            }
        }
    } catch (error) {
        if (error.name === 'Error' && error.message === 'time') {
            await message.reply({
                embeds: [createErrorEmbed('Reset cancelled - confirmation timeout')]
            });
        } else {
            console.error('Reset all users error:', error);
            await message.reply({
                embeds: [createErrorEmbed('Failed to reset users. Please try again later.')]
            });
        }
    }
}

// Error handling
client.on('error', (error) => {
    console.error('Discord client error:', error);
});

process.on('unhandledRejection', (error) => {
    console.error('Unhandled promise rejection:', error);
});

// Login to Discord
if (!DISCORD_TOKEN) {
    console.error('❌ DISCORD_TOKEN is required in environment variables');
    process.exit(1);
}

client.login(DISCORD_TOKEN).catch((error) => {
    console.error('❌ Failed to login to Discord:', error);
    process.exit(1);
}); 
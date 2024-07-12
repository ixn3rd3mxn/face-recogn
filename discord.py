from discordwebhook import Discord

discord = Discord(url="https://discord.com/api/webhooks/1257947616377966733/td3usfNIUCpNTtJHGsqCc5_dOFHwwlOjJiuU49YQybKFYsnnnHtf7cS_4q_hqDUrUw58")
discord.post(
    embeds=[{"title": "โหลครับ โหลครับ", "โหลครับ โหลครับ": "Embed description"}],
)
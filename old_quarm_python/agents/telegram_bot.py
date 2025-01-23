import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config.settings import TELEGRAM_BOT_TOKEN, USE_MEMORY
from agents.swarm import AgentSwarm

class TelegramBot:
    def __init__(self):
        self.swarm = AgentSwarm()
        self.app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Add handlers
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /start is issued."""
        await update.message.reply_text(
            "👋 Welcome to the AI Agent Swarm!\n\n"
            "I'm here to help answer your questions using a swarm of specialized AI agents.\n"
            "Just send me your query and I'll process it.\n\n"
            "Example: 'Explain the concept of quantum computing'"
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process user messages."""
        try:
            await update.message.chat.send_action("typing")
            
            # Pass the Telegram user ID to maintain separate conversation histories
            response = await self.swarm.process_query(
                update.message.text, 
                telegram_mode=True,
                user_id=str(update.effective_user.id)
            )
            
            if response:
                if len(response) > 4096:
                    for i in range(0, len(response), 4096):
                        await update.message.reply_text(response[i:i+4096])
                else:
                    await update.message.reply_text(response)
            else:
                await update.message.reply_text("I couldn't generate a response. Please try again.")
                
        except Exception as e:
            await update.message.reply_text(
                f"❌ Sorry, an error occurred: {str(e)}\n"
                "Please try again later."
            )

    def run(self):
        """Start the bot."""
        print("Starting Telegram bot...")
        # Start the memory cleanup task if memory is enabled
        if USE_MEMORY:
            self.swarm.memory.start_cleanup()
        self.app.run_polling() 
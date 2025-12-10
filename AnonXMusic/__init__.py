from AnonXMusic.core.bot import Anony
from AnonXMusic.core.dir import dirr
from AnonXMusic.core.git import git
from AnonXMusic.core.userbot import Userbot
from AnonXMusic.misc import dbb, heroku

from .logging import LOGGER

# Initialize core features
dirr()
git()
dbb()
heroku()

# Initialize main app and userbot
app = Anony()
userbot = Userbot()

# Do NOT instantiate platform APIs here to avoid circular imports
# Import them only where needed

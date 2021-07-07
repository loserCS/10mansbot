
<img src="assets/logo/rounded-logo.png" alt="10-Man Queues" align="right" width="50" height="50"/>

# CS:GO Queue Bot &ensp; 
*A Discord bot to manage and setup CS:GO games*

This script uses the Discord Python API via a bot to manage queues of CS:GO players who want to play with other Discord server members. It is complete with a queueing system, team drafter, map drafter and a link to a unique PopFlash lobby.




*Note that currently the `mdraft` command depends on custom emojis to be used as buttons which are hardcoded [here](https://github.com/loserCS/10mansbot/blob/main/qbot/cogs/mapdraft.py#L20). As of right now you will need to make the emojis yourself and replace the emoji code in the map objects there.*

## Commands
`q!help` **-** Display help menu<br>

`q!about` **-** Display basic info about this bot<br>

`q!join` **-** Join the queue<br>

`q!leave` **-** Leave the queue<br>

`q!view` **-** Display who is currently in the queue<br>

`q!remove <mention>` **-** Remove the mentioned user from the queue (must have server kick perms)<br>

`q!empty` **-** Empty the queue (must have server kick perms)<br>

`q!cap <integer>` **-** Set the capacity of the queue to the specified value (must have admin perms)<br>
*This command is only available when the generic argument is set to true* 

`q!tdraft` **-** Start (or restart) a team draft from the last popped queue<br>

`q!mdraft` **-** Start (or restart) a map draft<br>

`q!setmp {+|-}<map name> ...` **-** Add or remove maps from the mdraft map pool (Must have admin perms)<br>

`q!popflash` **-** Link the server's designated PopFlash lobby<br>

`q!donate` **-** Link the bot's donation link<br>

`q!remind` **-** Set a reminder to ping you after specified time<br>

print("This reddit bot looks for mentions of TagPro maps that are NOT links,\n"
	  "and posts images of those maps as a comment.\n"
	  "It grabs the maps from the TagPro wiki /maps\n"
	  "It looks for submissions in subreddits in the 'subs' variable in this script\n"
	  "\n"
	  "This bot is created and currently maintained by Ko (/u/Wilcooo)\n")


VERSION = "0.1"

import praw     # reddit API
import re       # Regex
import secret   # passwords and bot secret stored seperately


# All subreddits to check
# True: The map-images are in the CSS of this sub
# False: No possibility of images in the comments
# As far as I know, only /r/TagPro has this.
subs = {'TagPro' : True,
		'ELTP' : False,
		'MLTP' : False,
		'NLTP' : False,
		'OLTP' : False,
		'USContenders' : False,
		'ChordContenders' : False,
		'OContenders' : False,
		'TPTourneys' : False,
		'ContenderCaptains' : False,
		'WorldContenders' : False,
		'HonkPro' : False,
		'CLTP' : False,
		'SOCL' : False,
		'OFM' : False,
		'eggleague' : False,
		'NFTL' : False,
		'ECLTP' : False,
		'TPLH' : False,
		'TPLH3' : False,
		'TPLH4' : False,
		'tagproracing' : False,
		'MSLTP' : False,
		'lrn2tagpro' : False,
		'TagProMeme' : False,
		'TagProCirclejerk' : False,
		'TagProIRL' : False,
		'CentraTP' : False,
		'OriginTP' : False,
		'PiMasterRace' : False,
		'RadiusTP' : False,
		'SphereMasterRace' : False,
		'OceanicTagPro' : False,
		'TagProTesting' : False,
		'TagProMapSharing' : False,
		}




print ("Logging in...")
reddit = praw.Reddit(
	username = secret.username,
	password = secret.password,
	client_id = secret.client_id,
	client_secret = secret.client_secret,
	user_agent = "mapbot "+VERSION)




# A list of the maps to look for, and their images.
maps = {}

maps_wiki = reddit.subreddit('tagpro').wiki['maps'].content_md

for m in re.findall(r"(\[\]\(([^\[\]\(\)]+)\#map-([a-z\d]+(?:-[a-z\d]+)*)\))", maps_wiki):
	image = m[0]
	link = m[1]
	name = m[2]

	maps[name] = { 'link':link, 'image':image, }




def check_sub(sub, post_limit=100, comment_limit=100):
	# Checks a sub's recent posts and comments for mapnames
	if type(sub) == str :
		sub = reddit.subreddit(sub)

	submissions = list(sub.new(limit=post_limit)) + list(sub.comments(limit=comment_limit))

	for submission in sorted(submissions, key=lambda submission: submission.created_utc):

		print('Checking ' + submission.id + ': ',end='')

		if submission.saved:
			# Find out if I have commented on it before:
			for reply in submission.replies:
				if reply.author == secret.username:
					my_reply = reply
					break
			else: my_reply = False

			if submission.edited < max(my_reply.edited, my_reply.created):
				print('Saved, so skip')
				continue   # Skip this submission

		else: my_reply = False

		if ( hasattr(submission,'body') ) :
			text = submission.body.lower()       # a comment's text
		else :
			text = submission.title.lower() + submission.selftext.lower()   # a post's title & text


		links = str(re.findall(r"\[([^\[\]]*)\] *\s? *\([^\(\)]+\)", text))   # Get all linked bits of text in 1 string

		# Replace all non-alphanumeric characters with dashes
		text = '-' + re.sub(r"\W", "-", text) + '-'
		links = '-' + re.sub(r"\W", "-", links) + '-'

		mentioned = []   # All mentioned maps in the submission

		has_unlinked = False
		has_linked = False


		for name in maps:
			if '-' + name.lower() + '-' in links:
				mentioned.append(name)
				has_linked = True
			elif '-' + name.lower() + '-' in text:
				mentioned.append(name)
				has_unlinked = True

		if has_unlinked:
			reply = 'Images of the maps you mentioned:  \n'
			if has_linked:
				reply += '*^\(one ^or ^more ^were ^not ^linked ^to\)*\n'
			

			if subs[sub.display_name] : # If the subreddit has the maps in its CSS
				i = 0
				while mentioned[i:i+4]:
					reply += '\n\n'

					for name in mentioned[i:i+4]:
						#  Add a column title
						reply += '| [**' + name.replace('-',' ').title() + '**](' + maps[name]['link'] + ')'

					# Add the markdown table shit (centered)
					reply += '\n' + '|:---:' * len(mentioned[i:i+4]) + '\n'

					for name in mentioned[i:i+4]:
						#  Add an image of the map
						reply += '|' + maps[name]['image']

					i += 4

			else:   # If the subreddit doesn't have the maps in its CSS
				for name in mentioned:
					reply += '\n* [**' + name.replace('-',' ').title() + '**](' + maps[name]['link'] + ')'

			reply += '\n\n***\n^This ^bot ^is ^created ^and ^maintained ^by ^Ko ^\( [^u/Wilcooo](https://www.reddit.com/message/compose/?to=Wilcooo "Send a PM") ^\)'
			
			if my_reply:
				my_reply.edit(reply)    ## Edit my existing comment
				print('EDITED comment')

			else:     ## Make a new comment

				try:
					submission.reply(reply)
				except praw.exceptions.APIException as e:
					if e.error_type == 'RATELIMIT':
						print('\n\nRATELIMIT, trying again next check-round\n\n')
					else: print('\n\nERROR TRYING TO REPLY!\n\terror: '+e)
				else:
					submission.save()
					print('REPLIED to comment')

		else: print('nothing')



def delete_downvoted():
	comments = reddit.user.me().comments.new(limit=None)

	for comment in comments:
	    if comment.score < 0:
	        comment.delete()
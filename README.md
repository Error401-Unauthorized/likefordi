# LikeForDi

This program is a like for DI bot to be used in groupme and uses the sharepoint REST API to update DI for a squad.

## How to use

There are four blank fields in the config.json:

1. To start, chose a name for your bot and enter it as the value for "bot-name".  This value is who FalconNet thinks signed someone's DI.  I used my name so the FalconNet admins wouldn't flag it as suspicious.
2. Go to https://dev.groupme.com/ and create an application for your bot.  Copy your access token into the value for "groupme-api-key".
3. Make a GET request to 'https://api.groupme.com/v3/groups?token="Your access token goes here"'.  In the returned info, search for you squads group.  Copy the returned group-id into the "group-id" field.
4. In the "lookup-table-location" field, notice how it references a file called lookup.  You will need to make a file with everyone's groupme id and sharepoint id separated by a colon.  For example: 38879355:4014.  Each pairing should have its own line.
   1. You can get all the groupme ids by sending a GET request to 'https://api.groupme.com/v3/groups/"Your group-id here"?token="Your access token here"'
   2. To get all the sharepoint ids, you can ask everyone in squad to send you theirs, or you can send an api request to sharepoint.  The api request should be to 'https://usafa0.sharepoint.com/sites/LoFiDI/_api/web/lists/GetByTitle('Cadet Roster')/Items?$filter=(pysw eq 'CS"Your squad number here"')' but to make it easy paste that in your browser and sort through the returned xml yourself.  The ID should be in the <d:Id m:type="Edm.Int32">\</d:Id\> tag.
5. Finally, for the "sharepoint-cookie",  use your browser to go to "https://usafa0.sharepoint.com/sites/LoFiDI/Lists/Cadet%20Roster/NoItems.aspx".  Go to Inspect Element, the Network tab, and then refresh the page.  Click on the first item that shows up.  At the bottom of the Headers tab, there should be a field called cookie.  Copy the whole value into the "sharepoint-cookie" field.  Since cookies expire regularly, you will have to do this about one a week.
6. To make the program live, update the field "simulate" from "1" to "0".

The program should now work.  The default behavior of the program is to only send one group message.  The field "annoying-level" will change that

### Annoying-level values

| Annoying level |                           Behavior                           |
| :------------: | :----------------------------------------------------------: |
|       1        |               Will send only one group message               |
|       2        |                 Will send two group messages                 |
|       3        | Will send two group messages and will dm group members who haven't signed |

## Development

If you would like to help to develop this project I would appreciate it.  Just submit a pull request with the changes.  Try to keep the code looking nice and to the same format.  I will try to put issues up that I think the project could use but you are welcome to help any part of it.
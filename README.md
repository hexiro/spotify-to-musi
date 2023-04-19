# spotify-to-musi

> Transfer your [Spotify](https://spotify.com) playlists to [Musi](https://feelthemusi.com).

![banner](./.github/assets/banner.png)

# Why Musi?

Musi allows you to listen to any song (video) from YouTube without being interrupted with ads like with Spotify.
As someone who doesn't have a music streaming subscription I prefer to use Spotify on Desktop and Musi on mobile,
so I created this app to transfer songs between the two.

# Spotify Credentials Setup

1. Navigate to https://developer.spotify.com/dashboard \
   ![Dashboard](./.github/assets/dashboard.png)
2. Create an app with the name & description of your choice.
   Make sure the callback URL is set to http://localhost:5000/callback/spotify \
   ![Create App](./.github/assets/create-an-app.png)
3. Open Settings \
    ![Open Settings](./.github/assets/open-settings.png)
4. View Client ID and Client Secret and store them in a safe place. \
   ![View Client Credentials](./.github/assets/view-client-credentials.png)
5. Initialize setup script with `spotify-to-musi setup` & enter Client ID and Client Secret \
   ![Setup](./.github/assets/setup.png)
6. Open the link (http://localhost:5000/callback/spotify) in your browser and authorize with Spotify \
   ![Authorize](./.github/assets/authorize.png)
7. Return to your terminal, and you should be successfully authorized! :3 \
    ![Successfully Authorized](./.github/assets/successfully-authorized.png)



# PyCharm Usage

If you're running pycharm, make sure `emulate terminal in output console` is enabled<br>

references:

- https://youtrack.jetbrains.com/issue/PY-43860
- https://rich.readthedocs.io/en/latest/introductin.html

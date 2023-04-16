# spotify-to-musi

> Transfer your [Spotify](https://spotify.com) playlists to [Musi](https://feelthemusi.com).

![banner](./.github/assets/banner.png)

# Why Musi?

Musi allows you to listen to any song (video) from YouTube without being interrupted with ads like with Spotify.
As someone who doesn't have a music streaming subscription I prefer to use Spotify on Desktop and Musi on mobile,
so I created this app to transfer songs between the two.

# Spotify API

1. Go to https://developer.spotify.com/dashboard/ \
   ![Dashboard](./.github/assets/dashboard.png)
2. Choose an app name and accept the terms and conditions. \
   ![CREATE AN APP](./.github/assets/create-an-app.png)
3. Set callback to http://localhost:5000/callback/spotify \
   ![Set Callback](./.github/assets/set-callback.png)
4. View Client ID and Client Secret \
   ![SHOW CLIENT SECRET](./.github/assets/show-client-secret.png)
5. Rename .env.example to .env and set secrets \
   ![.env file](./.github/assets/dotenv-file.png)
6. Upon running the script for the first time, you will be prompted with something that looks like this: \
   ![first time setup](./.github/assets/first-time-setup.png)
7. Click the URL, Sign In if you need to and proceed until you see a page that looks like this: \
   ![img.png](.github/assets/example.com.png)
8. Copy the URL of the page you were redirected to and paste it into the console of the program and enter

# PyCharm Usage

If you're running pycharm, make sure `emulate terminal in output console` is enabled<br>

references:

- https://youtrack.jetbrains.com/issue/PY-43860
- https://rich.readthedocs.io/en/latest/introductin.html

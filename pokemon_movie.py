from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os, argparse, time

class Downloader:

    def __init__(self, movie_url="", clean=True):
        self.base_download_dir = "/Users/sylvain/Documents/dev/pokemon_movie/download"
        self.selenium_driver_path = "/Users/sylvain/Documents/dev/selenium_driver/chromedriver"
        self.m3u8_name = movie_url.split('/')[-1]
        self.full_download_dir = os.path.join(self.base_download_dir, movie_url.split('/')[-2])
        self.web_driver = None

        self.init_selenium()
        print("1 - Downloading playlist m3u8")
        self.do_download(movie_url)
        print("2 - Downloading TS files")
        self.download_movie(movie_url)
        print("3 - Concatenate TS files")
        self.concatenate_ts()
        if clean:
            print("4 - Cleaning tmp files")
            self.clean_files()
        self.web_driver.Quit()

    def init_selenium(self):
        if not os.path.exists(self.base_download_dir):
            os.mkdir(self.base_download_dir)
        if not os.path.exists(self.full_download_dir):
            os.mkdir(self.full_download_dir)
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--verbose')
        chrome_options.add_experimental_option("prefs", {
                "download.default_directory": self.full_download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing_for_trusted_sources_enabled": False,
                "safebrowsing.enabled": False
        })
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        self.web_driver = webdriver.Chrome(self.selenium_driver_path)
        self.enable_download_headless()

    def enable_download_headless(self):
        self.web_driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
        params = {'cmd':'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': self.full_download_dir}}
        self.web_driver.execute("send_command", params)

    def do_download(self, url_to_download):
        self.web_driver.get(url_to_download)
        self.download_wait(url_to_download)

    def download_movie(self, movie_url):
        base_movie_url = movie_url.replace(self.m3u8_name, "")

        files_to_concatenate = open(os.path.join(self.full_download_dir, "ts_list.txt"), 'w')

        with open(os.path.join(self.full_download_dir, self.m3u8_name), 'r') as fd:
            playlist_content = fd.readlines()
        for line in playlist_content:
            if "playlist" in line:
                line = line.replace('\n', '')
                files_to_concatenate.write("file '" + line + "'\n")
                self.do_download(base_movie_url + line)   
        files_to_concatenate.close()

    def download_wait(self, url_to_download):
        dl_wait = True
        file_to_download = url_to_download.split('/')[-1]
        while dl_wait:
            time.sleep(0.5)
            files = os.listdir(self.full_download_dir)
            if file_to_download in files:
                dl_wait = False
         
    def concatenate_ts(self):
        os.system("ffmpeg -f concat -i " + os.path.join(self.full_download_dir, "ts_list.txt") + " -c copy " + os.path.join(self.full_download_dir, self.m3u8_name.replace(".m3u8", "") + "_concatenate.mp4"))

    def clean_files(self):
        os.system("rm " + os.path.join(self.full_download_dir, "*.ts") + ' ' + os.path.join(self.full_download_dir, "*.txt") + ' ' + os.path.join(self.full_download_dir, "*.m3u8"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download movie from Pokemon TV")
    parser.add_argument("--url", type=str, help="Playlist Movie URL (.m3u8)")
    args = parser.parse_args()

    if args.url:
        Downloader(args.url, clean=True)
    else:
        parser.print_help()
import json

import rclone


class RcloneUtil:
    def __init__(self, cfg_path):
        self.cfg_path = r'' + cfg_path

        with open(cfg_path) as f:
            cfg = f.read()
            f.close()
        self.rclone_base = rclone.with_config(cfg)

    def copy_file_by_url(self, url, dest):
        return self.rclone_base.run_cmd(
            command='copyurl',
            extra_args=[url, dest]
        )

    def get_files_from_remote(self, source) -> list:
        result = self.rclone_base.run_cmd(
            command='lsjson',
            extra_args=[source]
        )

        if not result.get('code'):
            files_str = result.get('out').decode('utf-8')
            return self.get_file_names(json.loads(files_str))

        return None

    @staticmethod
    def get_file_names(files):
        return [item.get('Name') for item in files]


util = RcloneUtil('/Users/odenypeter/.config/rclone/rclone.conf')
print(util.get_files_from_remote('demo-1-1:'))

import requests

resp = requests.get('https://csgo.gamersclub.gg/lobby/demoDownload/15859459/')
print(resp.text)
# -v --drive-stop-on-upload-limit --fast-list --drive-chunk-size=256M --buffer-size=256M --no-clobber --retries 1
Adds a new node `RemoteSaveImage` which saves images generated on a remote server to local machine directly, thus eliminating the need to first save generated images on the remote server's hard disk and then download them to your local machine though `ftp` etc.

#Usage
* two copies of this repository is needed: (1) git clone this repository under `custom_nodes/` on the remote server
  (2) git clone this repository anywhere on your local machine
* in `config.yaml`, replace `server_host` to the public IP address of the remote server where ComfyUI web service is running, and replace `server_port` to some publicly visible port available on the remote server (this port is used for image transfer)
* start ComfyUI web service as usual on the remote server
* run `python client.py` under the root directory of this repository **on your local machine**

The added node `RemoteSaveImage` can be found under the `Image` category. Any image input into `RemoteSaveImage` node will be saved under the output directory on your local machine specified by the node's `output_dir` property. Non-existent directories will be created.
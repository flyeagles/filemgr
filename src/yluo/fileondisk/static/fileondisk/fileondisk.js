import {setupClipMonitor} from './clip_monitor.js'; // or './module'

$(function () {  // on page load
    
    const numberWithCommas = (x) => {
        return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    };

    var func_assemble_vol_info = function(vol_model) {
        return "Total Size: " + numberWithCommas(vol_model.get("size")) + " bytes.\n" + 
            "Free Size: " +  numberWithCommas(vol_model.get("size_free")) + " bytes.";
    };

    var gActiveNodeFullVolPath = '';

    // Create the tree inside the <div id="tree"> element.
    var init_folder_tree = {
        extensions: ["edit", "filter"],
        tooltip: function (event, data) {
            // Create dynamic tooltips
            return data.node.title + " (" + data.node.data.serial_no + ")";
        },
        source: [
            // {title: "FODM", lazy: true, folder: true,},
        ],

        click: function (event, data) {
            var node = data.node,
                // Only for click and dblclick events:
                // 'title' | 'prefix' | 'expander' | 'checkbox' | 'icon'
                targetType = data.targetType;
            if (node.data.item_type == 'fold') {
                gActiveNodeFullVolPath = node.data.fullvolpath;

                // need refresh the file list tree with the data for this folder
                var folders = new Folder(data.node.data.fullvolpath, data.node.data.volume_model_id);
                folders.fetch_render(null, node.data.disk_model_id, gFile_list, false);

                var volume_data = gAll_volume_map[node.data.volume_model_id];
                document.getElementById("volume_info_text").value = func_assemble_vol_info(volume_data);

            } else if (node.data.item_type == 'disk') {
                document.getElementById("volume_info_text").value = "Volume Information";
            } else {
                var volume_data = gAll_volume_map[node.data.volume_model_id];
                document.getElementById("volume_info_text").value = func_assemble_vol_info(volume_data);
            }


            var disk = gDiskcollection.get(node.data.disk_model_id);
            document.getElementById("disk_info_text").value = disk.get("SMART_info");

            // we could return false to prevent default handling, i.e. generating
            // activate, expand, or select events
            return true;
        },

        lazyLoad: function (event, data) {
            // Pass on a deferred promise from another method:
            //  data.result = $.getJSON("ajax-sub2.json");
            // Immediately return a deferred and resolve it as soon as data is available:

            var dfd = new $.Deferred();
            data.result = dfd.promise();

            if (data.node.data.item_type == 'disk') {
                // need expand to get volumes under this disk
                var volumes = new VolumeCollection(data.node.data.serial_no);
                volumes.fetch_render(dfd, data.node.data.disk_model_id);
                /*dfd.resolve([
                    { title: data.node.title + "1", lazy: true, folder: true },
                    { title: "node 2"}
                ]);*/

            } else if (data.node.data.item_type == 'volume') {
                // need get root folders under this volume
                var rootfolders = new RootCollection(data.node.data.vol_id);
                rootfolders.fetch_render(dfd, data.node.data.disk_model_id);
            } else if (data.node.data.item_type == 'fold') {
                var folders = new Folder(data.node.data.fullvolpath, data.node.data.volume_model_id);
                folders.fetch_render(dfd, data.node.data.disk_model_id, gFile_list, true);
            } else {
                dfd.resolve([]);
            };

        },
    };
    $("#folder_tree").fancytree(init_folder_tree);

    console.log("Hello world");

    var gVolume_disk_map = {};  // map from volume ID to disk ID
    var gAll_volume_map = {};   // map from volume ID to volume Model object

    var init_file_list = {
        extensions: ["filter"],
        tooltip: function (event, data) {
            // Create dynamic tooltips
            return data.node.title + " (" + data.node.data.serial_no + ")";
        },
        source: [],

        click: function (event, data) {
            var node = data.node,
                // Only for click and dblclick events:
                // 'title' | 'prefix' | 'expander' | 'checkbox' | 'icon'
                targetType = data.targetType;

            gActiveNodeFullVolPath = node.data.fullvolpath;

            var filedups = new FileDuplicates(node.data.fullvolpath);
            filedups.fetch_render("fetching folder");

            var filedetail = gFile_obj_dict[node.title];
            var mod_date = new Date(filedetail.get("mod_time") * 1000);
            document.getElementById("file_info_text").value = "Size: " + numberWithCommas(filedetail.get("size")) + " bytes\n" +
                "Mod time: " + mod_date;

            // we could return false to prevent default handling, i.e. generating
            // activate, expand, or select events
            return true;
        },
    };
    $("#file_list").fancytree(init_file_list);
    var gFile_list = $("#file_list").fancytree("getTree");



    // Note: Loading and initialization may be asynchronous, so the nodes may not be accessible yet.
    var gTree = $("#folder_tree").fancytree("getTree");


    document.getElementById("check_scroll").onclick = function () {
        var scr_ele = document.getElementById("folder_tree_scr");
        console.log("Scroll position");
        console.log(scr_ele.scrollTop);
        console.log(scr_ele.scrollHeight);
        console.log(scr_ele.clientHeight);
        scr_ele.scrollTo(0, 180);
    };


    var ModelForExplorer = Backbone.Model.extend({
        setSelect: function (select_item) {
            console.error(select_item);
            this.select_item = select_item;
        },

        url: function () {
            var self = this;
            console.log("Fetch");
            console.error(self.select_item);
            return 'explore/' + self.select_item + '/';
        },
    });

    var gExplorer = new ModelForExplorer();

    var open_explorer = function(activeNodeFullVolPath) {
        if (activeNodeFullVolPath == '') {
            return;
        }

        gExplorer.setSelect(activeNodeFullVolPath);
        gExplorer.fetch();
    };

    document.getElementById("open_explorer").onclick = function(event) {
        open_explorer(gActiveNodeFullVolPath);
    };

    document.addEventListener('keyup', (event) => {
        if (event.code == 'ArrowUp') {
            open_explorer(gActiveNodeFullVolPath);
        }
    });
    
    
    /* ===========================================
        Disk and Volume List Section
    ===========================================*/

    // Backbone sample code
    var Disk = Backbone.Model.extend({
    });

    var DiskCollection = Backbone.Collection.extend({
        // el - stands for element. Every view has an element associated with HTML content, will be rendered. 
        model: Disk,
        url: 'disks/',

        fetch_render: function (view) {
            var self = this;
            this.fetch({
                success: function (collection, response, options) {
                    view.render(collection);
                },
            });
        },
    });

    var gPresent_disk_set = new Set();
    var PresentDiskCollection = Backbone.Collection.extend({
        // el - stands for element. Every view has an element associated with HTML content, will be rendered. 
        model: Disk,
        url: 'presentdisks/',

        fetch_add: function () {
            var self = this;
            this.fetch({
                success: function (collection, response, options) {
                    _.each(collection.models, function (model) {
                        gPresent_disk_set.add(model.get("serial_no"));
                    });

                    // move this here to ensure the timing of two fetch is correct.
                    gDiskcollection.fetch_render(gDiskview);
                },
            });
        },
    });
    var gPres_disk_coll = new PresentDiskCollection();
    gPres_disk_coll.fetch_add();
    
    var DiskCollectionView = Backbone.View.extend({
        // el: "#stock_transaction_sect",
        initialize: function (attrs) {
            var self = this;
            // self.model = attrs['model'];
            // self.render();   
        },

        render: function (diskcollection) {
            var self = this;
            var activeNode = gTree.getRootNode();

            var newnode;
            _.each(diskcollection.models, function (model) {

                // Append a new child node
                var icon_url = gPresent_disk_set.has(model.get("serial_no")) ?
                    "/static/fileondisk/icons/ic_computer_black_24px.svg" :
                    "/static/fileondisk/icons/turn-off-icon-24.png";

                icon_url = model.get("is_raid1") ==0 ? icon_url: "/static/fileondisk/icons/Places-document-multiple-icon-24.png"; 

                newnode = activeNode.addChildren({
                    title: model.get("disk_model"),
                    folder: true,
                    lazy: true,
                    serial_no: model.get("serial_no"),
                    icon: icon_url,
                    item_type: "disk",
                    disk_model_id: model.cid,
                });
                
                newnode.setExpanded();
            });
            newnode.makeVisible();
            newnode.scrollIntoView();
            //console.log(self.model.toJSON());
            // var output=self.template({'stock_transaction_list': self.model.toJSON() });
            //self.$el.html(output);

            return self;
        },
    });

    var Volume = Backbone.Model.extend({
    });

    var VolumeCollection = Backbone.Collection.extend({
        model: Volume,
        initialize: function (sno) {
            this.serial_no = sno;
        },

        url: function () {
            var self = this;
            return 'disks/' + self.serial_no + '/volumes/';
        },

        fetch_render: function (dfd, in_disk_model_id) {
            var self = this;
            this.fetch({
                success: function (collection, response, options) {
                    var nodes = [];
                    _.each(collection.models, function (model) {
                        gAll_volume_map[model.get("id")] = model;
                        nodes.push({
                            title: model.get("volume_name"),
                            lazy: true, folder: true,
                            vol_id: model.get("id"),
                            icon: "/static/fileondisk/icons/ic_dvr_black_24px.svg",
                            item_type: "volume",
                            disk_model_id: in_disk_model_id,
                            volume_model_id: model.get("id"),
                        });

                        gVolume_disk_map[model.get("id")] = in_disk_model_id;
                    });

                    dfd.resolve(nodes);
                },

                error: function (collection, response, options) {
                    console.error("Error of fetching roots!");
                    dfd.resolve([]);
                },
            });
        },

    });

    var FileInfo = Backbone.Model.extend({
    });

    var RootFolder = Backbone.Model.extend({
        initialize: function (fullvolpath) {
            this.id = '123';
            this.fullvolpath = fullvolpath;
        },

        defaults: {
            id: '',
        },

        urlRoot: function () {
            var self = this;
            return 'root/' + self.fullvolpath;
        },
    });
    
    document.getElementById("unmonitor_root").onclick = function(event) {
        console.info(gActiveNodeFullVolPath);
        rootFolder = new RootFolder(gActiveNodeFullVolPath);
        rootFolder.destroy({
            success: function() {
                location.reload();
            },
        });
    };
    

    var RootCollection = Backbone.Collection.extend({
        model: RootFolder,
        initialize: function (vid) {
            this.volume_id = vid;
        },

        url: function () {
            var self = this;
            return 'volumes/' + self.volume_id + '/';
        },

        fetch_render: function (dfd, in_disk_model_id) {
            var self = this;
            this.fetch({
                success: function (collection, response, options) {
                    var nodes = []
                    _.each(collection.models, function (model) {
                        nodes.push({
                            title: model.get("fname"),
                            lazy: true,
                            folder: true,
                            fullvolpath: model.get("fullvolpath"),
                            // icon: "/static/fileondisk/icons/ic_dvr_black_24px.svg",
                            item_type: "fold",
                            disk_model_id: in_disk_model_id,
                            volume_model_id: self.volume_id,
                        });
                    });
                    dfd.resolve(nodes);
                },

                error: function (collection, response, options) {
                    console.error("Error of fetching roots!");
                    dfd.resolve([]);
                },
            });
        },
    });

    var gDiskview = new DiskCollectionView({});

    var gDiskcollection = new DiskCollection();
    // diskcollection.fetch_render(diskview);  move to fetch/success of presentdisks.


    document.getElementById("disk_info_text").value = "Disk information";

    /* ===========================================
        In-Folder File List Section
    ===========================================*/

    var gFile_obj_dict = {};

    var Folder = Backbone.Collection.extend({
        model: FileInfo,
        initialize: function (fullvolpath, volume_id) {
            this.fullvolpath = fullvolpath;
            this.volume_id = volume_id;
        },

        url: function () {
            var self = this;
            return 'folders/' + self.fullvolpath + '/';
        },

        fetch_render: function (dfd, in_disk_model_id, file_list, expand_tree) {
            var self = this;
            this.fetch({
                success: function (collection, response, options) {
                    file_list.clear();
                    var file_list_root_node = file_list.getRootNode();

                    var file_obj_dict = {};
                    var nodes = []
                    _.each(collection.models, function (model) {
                        if (model.get('file_type') != 'fold') {

                            file_obj_dict[model.get("fname")] = model;
                            file_list_root_node.addNode({
                                title: model.get("fname"),
                                lazy: false,
                                folder: false,
                                fullvolpath: model.get("fullvolpath"),
                                // icon: "/static/fileondisk/icons/ic_dvr_black_24px.svg",
                                item_type: model.get('file_type'),
                                disk_model_id: in_disk_model_id,
                                volume_model_id: self.volume_id,
                            });
                        } else {
                            if (expand_tree) {
                                nodes.push({
                                    title: model.get("fname"),
                                    lazy: true,
                                    folder: true,
                                    fullvolpath: model.get("fullvolpath"),
                                    // icon: "/static/fileondisk/icons/ic_dvr_black_24px.svg",
                                    item_type: "fold",
                                    disk_model_id: in_disk_model_id,
                                    volume_model_id: self.volume_id,
                                });
                            };
                        }
                    });
                    if (expand_tree)
                        dfd.resolve(nodes);

                    file_list.render();
                },

                error: function (collection, response, options) {
                    console.error("Error of fetching folder!");
                    dfd.resolve([]);
                },
            });
        },

    });

    /* ===========================================
        Duplicate File List Section
    ===========================================*/

    var init_file_dup_list = {
        extensions: ["filter"],
        tooltip: function (event, data) {
            // Create dynamic tooltips
            return data.node.title + " (" + data.node.data.serial_no + ")";
        },
        source: [],

        click: function (event, data) {
            var node = data.node,
                // Only for click and dblclick events:
                // 'title' | 'prefix' | 'expander' | 'checkbox' | 'icon'
                targetType = data.targetType;

            if (node.data.item_type != "disknode" && node.data.item_type != "volumenode") {
                gActiveNodeFullVolPath = node.data.fullvolpath;

                var filedetail = gDup_file_obj_dict[node.data.fullvolpath];
                var mod_date = new Date(filedetail.get("mod_time") * 1000);
                document.getElementById("dup_file_info_text").value = "Size: " + numberWithCommas(filedetail.get("size")) + " bytes\n" +
                    "Mod time: " + mod_date;
    
                document.getElementById("dup_file_path").value = filedetail.get("folder");

                var folders = new Folder(filedetail.get("folder"), data.node.data.volume_id);
                folders.fetch_render(null, node.data.disk_model_id, dup_folder_tree, false);

                var volume_data = gAll_volume_map[node.data.volume_id];
                document.getElementById("tar_volume_info_text").value = func_assemble_vol_info(volume_data);

            } else if (node.data.item_type == "volume") {
                gActiveNodeFullVolPath = node.data.fullvolpath;

                var volume_data = gAll_volume_map[node.data.volume_id];
                document.getElementById("tar_volume_info_text").value = func_assemble_vol_info(volume_data);
            }

            var disk = gDiskcollection.get(node.data.disk_model_id);
            document.getElementById("tar_disk_info_text").value = disk.get("SMART_info");
            
            // we could return false to prevent default handling, i.e. generating
            // activate, expand, or select events
            return true;
        },
    };
    $("#duplicate_files").fancytree(init_file_dup_list);
    var gDuplicate_files = $("#duplicate_files").fancytree("getTree");

    var gDup_file_obj_dict = {};     // all the file objects in the Dup File List tree

    var dup_file_list_fetch_render = function (msg_part) {
        var self = this;
        this.fetch({
            success: function (collection, response, options) {

                document.getElementById("dup_file_count").value = collection.models.length;
    
                gDuplicate_files.clear();
                var dup_file_list_root_node = gDuplicate_files.getRootNode();
                gDup_file_obj_dict = {};

                var dup_disk_file_map = {};
                var disk_id_set = new Set();

                var firstitem = true;

                _.each(collection.models, function (model) {

                    if (model.get("fullvolpath") == self.fullvolpath) {
                        return;
                    }

                    gDup_file_obj_dict[model.get("fullvolpath")] = model;
                    var volume_id = model.get("volume_id");
                    var disk_mid = gVolume_disk_map[volume_id];

                    disk_id_set.add(disk_mid);
                    if (dup_disk_file_map.hasOwnProperty(""+disk_mid)) {
                        var vol_file_map = dup_disk_file_map[""+disk_mid];
                        if (vol_file_map.hasOwnProperty(volume_id)) {
                            vol_file_map[volume_id].push(model);
                        } else {
                            vol_file_map[volume_id] = [model]
                        }
                    } else {
                        var vol_file_map = {};
                        vol_file_map[volume_id] =  [gAll_volume_map[volume_id], model];
                        dup_disk_file_map[""+disk_mid] = vol_file_map;
                    };

                    if (firstitem) {
                        firstitem = false;

                        var volume_data = gAll_volume_map[volume_id];
                        document.getElementById("tar_volume_info_text").value = func_assemble_vol_info(volume_data);

                        var disk = gDiskcollection.get(disk_mid);
                        document.getElementById("tar_disk_info_text").value = disk.get("SMART_info");

                        var filedetail = model;
                        var mod_date = new Date(filedetail.get("mod_time") * 1000);
                        document.getElementById("dup_file_info_text").value = "Size: " + numberWithCommas(filedetail.get("size")) + " bytes\n" +
                            "Mod time: " + mod_date;
                            }                        
                });

                var disk_id_list = Array.from(disk_id_set);
                _.each(disk_id_list, function(disk_mid) {
                    var disk_obj = gDiskcollection.get(disk_mid)

                    var icon_url = gPresent_disk_set.has(disk_obj.get("serial_no")) ?
                        "/static/fileondisk/icons/ic_computer_black_24px.svg" :
                        "/static/fileondisk/icons/turn-off-icon-24.png";

                    var disk_root_node = dup_file_list_root_node.addNode({
                        title: disk_obj.get("disk_model"),
                        lazy: false,
                        folder: false,
                        serial_no: disk_obj.get("serial_no"),
                        icon: icon_url,
                        item_type: "disknode",
                        disk_model_id: disk_mid,
                    });
    
                    var vol_file_map = dup_disk_file_map["" + disk_mid];
                    _.each(Object.getOwnPropertyNames(vol_file_map), function (propName) {
                        var volume_files = vol_file_map[propName];
                        var volume_id = volume_files[0].get("id");
                        var vol_root_node = disk_root_node.addNode({
                            title: volume_files[0].get("volume_name"),
                            lazy: false,
                            folder: false,
                            volume_id: volume_id,
                            icon: "/static/fileondisk/icons/ic_computer_dvr_24px.svg",
                            item_type: "volumenode",
                            disk_model_id: disk_mid,
                        });

                        var vol_file_len = volume_files.length;
                        for (var index = 1; index < vol_file_len; index++) {
                            // skip first item, which is the volume information
                            var fileinfo = volume_files[index];

                            var this_node = vol_root_node.addNode({
                                title: fileinfo.get("fname"),
                                lazy: false,
                                folder: false,
                                fullvolpath: fileinfo.get("fullvolpath"),
                                // icon: "/static/fileondisk/icons/ic_dvr_black_24px.svg",
                                item_type: fileinfo.get('file_type'),
                                disk_model_id: disk_mid,
                                volume_id: volume_id,
                            });
                        };

                        vol_root_node.setExpanded();
                    });

                    disk_root_node.setExpanded();

                });

                gDuplicate_files.render();
            },

            error: function (collection, response, options) {
                console.error("Error of " + msg_part);
            },
        });
    };

    var FileDuplicates = Backbone.Collection.extend({
        model: FileInfo,
        initialize: function (fullvolpath) {
            this.fullvolpath = fullvolpath;
        },

        url: function () {
            var self = this;
            return 'file/' + self.fullvolpath + '/';
        },

        fetch_render: dup_file_list_fetch_render,
    });



    /* ===========================================
        Duplicate Target Folder Content  Section
    ===========================================*/

    $("#dup_folder").fancytree({
        extensions: ["filter"],
        tooltip: function (event, data) {
            // Create dynamic tooltips
            return data.node.title + " (" + data.node.key + ")";
        },
        source: [],

        click: function (event, data) {
            var node = data.node,
                // Only for click and dblclick events:
                // 'title' | 'prefix' | 'expander' | 'checkbox' | 'icon'
                targetType = data.targetType;

            gActiveNodeFullVolPath = node.data.fullvolpath;

            return true;
        },
        
    });
    var dup_folder_tree = $("#dup_folder").fancytree("getTree");
    





    /* ===========================================
        Search File Handling
    ===========================================*/

    var FileSearchResults = Backbone.Collection.extend({
        model: FileInfo,
        initialize: function (searchtext) {
            this.searchtext = searchtext;
            this.fullvolpath = "";   // to accommodate dup_fie_list processing
        },

        url: function () {
            var self = this;
            return 'search/' + self.searchtext + '/';
        },

        fetch_render: dup_file_list_fetch_render,
    });


    
    var search_file = function () {
        var term = document.getElementById("search_file_input").value
        var searchresults = new FileSearchResults(term);
        searchresults.fetch_render("Search File");
    };
    
    document.getElementById("search_file_input").onfocus = function () {
        document.getElementById("search_file_input").value = "";
    };

    $("#search_file_input").on('keyup', function (key) {
        if (key.keyCode == 13) { // ENTER key
            search_file();
        };
    });

    document.getElementById("search_button").onclick = function () {
        search_file();
    };

    /* ===========================================
        Find files duplicated with RAID1 items
    ===========================================*/

    var Raid1DupFileSearchResults = Backbone.Collection.extend({
        model: FileInfo,
        initialize: function (searchfolder) {
            this.searchfolder = searchfolder;
            this.fullvolpath = "";   // to accommodate dup_fie_list processing
        },

        url: function () {
            var self = this;
            return 'findraid1dup/' + self.searchfolder + '/';
        },

        fetch_render: dup_file_list_fetch_render,
    });

    var find_raid1_dup_file = function () {
        var term = document.getElementById("find_dup_file_input").value
        var searchresults = new Raid1DupFileSearchResults(term);
        searchresults.fetch_render("Find RAID1 Duplicates");
    };
    
    document.getElementById("find_dup_file_input").onfocus = function () {
        document.getElementById("find_dup_file_input").value = "";
    };

    $("#find_dup_file_input").on('keyup', function (key) {
        if (key.keyCode == 13) { // ENTER key
            find_raid1_dup_file();
        };
    });

    document.getElementById("raid1_dup_search_button").onclick = function () {
        find_raid1_dup_file();
    };
    

    /* ===========================================
        Delete files duplicated with RAID1 items
    ===========================================*/

    var Raid1DupFileDeleteResults = Backbone.Collection.extend({
        model: FileInfo,
        initialize: function (searchfolder) {
            this.searchfolder = searchfolder;
            this.fullvolpath = "";   // to accommodate dup_fie_list processing
        },

        url: function () {
            var self = this;
            return 'deletedup/' + self.searchfolder + '/';
        },

        fetch_render: dup_file_list_fetch_render,
    });

    var delete_raid1_dup_file = function () {
        var term = document.getElementById("find_dup_file_input").value
        var searchresults = new Raid1DupFileDeleteResults(term);
        searchresults.fetch_render("Delete RAID1 Duplicates");
    };
    
    document.getElementById("raid1_dup_delete_button").onclick = function () {

        if (window.confirm("Do you really want to delete those files?")) {
            delete_raid1_dup_file();
        } else {
            find_raid1_dup_file();
        }
    };


    var monitorClipWS = setupClipMonitor(search_file);
    monitorClipWS();

});



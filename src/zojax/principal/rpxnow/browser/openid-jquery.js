/*
Simple RpxNow Plugin
http://code.google.com/p/rpxnow-selector/

This code is licenced under the New BSD License.
*/

var providers_large = {
    google: {
        name: 'Google',
        url: 'https://www.google.com/accounts/o8/id'
    },
    yahoo: {
        name: 'Yahoo',      
        url: 'http://yahoo.com/'
    },    
    aol: {
        name: 'AOL',     
        label: 'Enter your AOL screenname.',
        url: 'http://rpxnow.aol.com/{username}/'
    },
    rpxnow: {
        name: 'RpxNow',     
        label: 'Enter your RpxNow.',
        url: null
    }
};
var providers_small = {
    myrpxnow: {
        name: 'MyRpxNow',
        label: 'Enter your MyRpxNow username.',
        url: 'http://{username}.myrpxnow.com/'
    },
    livejournal: {
        name: 'LiveJournal',
        label: 'Enter your Livejournal username.',
        url: 'http://{username}.livejournal.com/'
    },
    flickr: {
        name: 'Flickr',        
        label: 'Enter your Flickr username.',
        url: 'http://flickr.com/{username}/'
    },
    technorati: {
        name: 'Technorati',
        label: 'Enter your Technorati username.',
        url: 'http://technorati.com/people/technorati/{username}/'
    },
    wordpress: {
        name: 'Wordpress',
        label: 'Enter your Wordpress.com username.',
        url: 'http://{username}.wordpress.com/'
    },
    blogger: {
        name: 'Blogger',
        label: 'Your Blogger account',
        url: 'http://{username}.blogspot.com/'
    },
    verisign: {
        name: 'Verisign',
        label: 'Your Verisign username',
        url: 'http://{username}.pip.verisignlabs.com/'
    },
    vidoop: {
        name: 'Vidoop',
        label: 'Your Vidoop username',
        url: 'http://{username}.myvidoop.com/'
    },
    verisign: {
        name: 'Verisign',
        label: 'Your Verisign username',
        url: 'http://{username}.pip.verisignlabs.com/'
    },
    claimid: {
        name: 'ClaimID',
        label: 'Your ClaimID username',
        url: 'http://claimid.com/{username}'
    }
};
var providers = $.extend({}, providers_large, providers_small);

var rpxnow = {

	cookie_expires: 6*30,	// 6 months.
	cookie_name: 'rpxnow_provider',
	cookie_path: '/',
	
	img_path: '@@/rpxnow_images/',

	input_id: null,
	provider_url: null,
	
    init: function(input_id) {
        
        var rpxnow_btns = $('#rpxnow_btns');
        
        this.input_id = input_id;
        
        $('#rpxnow_choice').show();
        $('#rpxnow_input_area').empty();
        
        // add box for each provider
        for (id in providers_large) {
        
           	rpxnow_btns.append(this.getBoxHTML(providers_large[id], 'large', '.gif'));
        }
        if (providers_small) {
            rpxnow_btns.append('<br/>');
        	
	    for (id in providers_small) {
	        rpxnow_btns.append(this.getBoxHTML(providers_small[id], 'small', '.ico'));
	    }
        }
        
        $('#rpxnow_form').submit(this.submit);
        
        var box_id = this.readCookie();
        if (box_id) {
            this.signin(box_id, true);
        }  
    },

    getBoxHTML: function(provider, box_size, image_ext) {            
        var box_id = provider["name"].toLowerCase();
        return '<a title="'+provider["name"]+'" href="javascript: rpxnow.signin(\''+ box_id +'\');"' +
        		' style="background: #FFF url(' + this.img_path + box_id + image_ext+') no-repeat center center" ' + 
        		'class="' + box_id + ' rpxnow_' + box_size + '_btn"></a>';    
    
    },

    /* Provider image click */
    signin: function(box_id, onload) {
    	var provider = providers[box_id];
  	if (! provider) {
  	    return;
  	}
		
	this.highlight(box_id);
	this.setCookie(box_id);
	this.provider_url = provider['url'];
		
	// prompt user for input?
	if (provider['label']) {
	    this.useInputBox(provider);
	} else {
	    this.setRpxNowUrl(provider['url']);
	    if (! onload) {
		$('#rpxnow_form').submit();
	    }
	}
    },

    /* Sign-in button click */
    submit: function() {        
    	var url = rpxnow.provider_url; 
    	if (url) {
    	    url = url.replace('{username}', $('#rpxnow_username').val());
    	    rpxnow.setRpxNowUrl(url);
    	}
    	return true;
    },
    setRpxNowUrl: function (url) {
        var hidden = $('#'+this.input_id);
    	if (hidden.length > 0) {
    	    hidden.attr('value', url);
    	} else {
    	    $('#rpxnow_form').append('<input type="hidden" id="' + this.input_id + '" name="' + this.input_id + '" value="'+url+'"/>');
    	}
    },

    highlight: function (box_id) {	
    	// remove previous highlight.
    	var highlight = $('#rpxnow_highlight');
    	if (highlight) {
    		highlight.replaceWith($('#rpxnow_highlight a')[0]);
    	}
    	// add new highlight.
    	$('.'+box_id).wrap('<div id="rpxnow_highlight"></div>');
    },

    setCookie: function (value) {
    
		var date = new Date();
		date.setTime(date.getTime()+(this.cookie_expires*24*60*60*1000));
		var expires = "; expires="+date.toGMTString();
		
		document.cookie = this.cookie_name+"="+value+expires+"; path=" + this.cookie_path;
    },
    readCookie: function () {
		var nameEQ = this.cookie_name + "=";
		var ca = document.cookie.split(';');
		for(var i=0;i < ca.length;i++) {
			var c = ca[i];
			while (c.charAt(0)==' ') c = c.substring(1,c.length);
			if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
		}
		return null;
    },
    useInputBox: function (provider) {
   	
		var input_area = $('#rpxnow_input_area');
		
		var html = '';
		var id = 'rpxnow_username';
		var value = '';
		var label = provider['label'];
		var style = '';
		
		if (label) {
			html = '<p>' + label + '</p>';
		}
		if (provider['name'] == 'RpxNow') {
			id = this.input_id;
			value = 'http://';
			style = 'background:#FFF url('+this.img_path+'rpxnow-inputicon.gif) no-repeat scroll 0 50%; padding-left:18px;';
		}
		html += '<input id="'+id+'" type="text" style="'+style+'" name="'+id+'" value="'+value+'" />' + 
					'<input id="rpxnow_submit" type="submit" value="Sign-In"/>';
		
		input_area.empty();
		input_area.append(html);

		$('#'+id).focus();
    }
};

$(document).ready(function() {
    rpxnow.init('rpxnow_identifier');
});

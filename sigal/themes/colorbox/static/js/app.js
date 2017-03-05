$(".gallery").colorbox({
  rel:"gallery",
  transition:"none",
  maxWidth: "90%",
  maxHeight: "90%",
  scalePhotos: true,
  current: "{current} / {total}",
  title: function () {
    title = this.title;
    if(this.hasAttribute("data-big")) {
      title += " (full size)".link(this.getAttribute("data-big"));
    }
    if(this.hasAttribute("data-date")) {
      title += this.getAttribute("data-date");
    }
    return title;
  },
  inline: function() {
    return this.hasAttribute("inline");
  }
});

$(document).bind('cbox_open', function(){
  $("#cboxOverlay, #colorbox").swipe({
    swipeLeft:function(event, direction, distance, duration, fingerCount) {
      $.colorbox.next();
    },
    swipeRight:function(event, direction, distance, duration, fingerCount) {
      $.colorbox.prev();
    },
    tap:function(event, target){
      $.colorbox.close()
    },
    excludedElements: $.fn.swipe.defaults.excludedElements + ", #colorbox"
  }).unbind("click");
});

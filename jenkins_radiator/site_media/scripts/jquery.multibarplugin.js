(function( $ ) {
  $.fn.multibarplugin = function(opts) {

	/***
	*	Author: Anthony Martin
	*	This plugin creates a multi bar graph with the following parameters:
	*	colors - [required] array of class names for the various bar colors
	*	roundRect - [optional] array of left and right class names for creating round rectangles on each end of bar graph
	*	textClass - [optional] array of class name to pass in if you want the text displayed on the bar graph... per bar text (only pass in for the bars you want
				ex: textClass: ["barGraphText","","barGraphText"] will show the text for the 1st and 3rd bars
	*
	*	Example Plugin Call: 
	*	$(".bargraph").multibarplugin({colors: ["successStatus", "failureStatus"], roundRect: ["barGraphLeft", "barGraphRight"], textClass: ["barGraphText"]});
	***/
  	
	var colors = opts.colors;
	var roundRect = opts.roundRect;
	var textClass = opts.textClass;
  
	this.each(function(index) {
		$(this).children("div").each(function(index) {
			var el = $(this);			
			el.addClass(colors[index]);
			el.css("width", $(this).text() + "%");
			if(roundRect){
				if(el.text() == 100){
					for(i=0; i < roundRect.length; i++){
						el.addClass(roundRect[i]);
						el.parent().addClass(roundRect[i]);
					}
				}
				else{
					if(index === 0){
						el.addClass(roundRect[index]);
						el.parent().addClass(roundRect[index]);
					}
					else if(index === colors.length - 1){
						el.addClass(roundRect[roundRect.length - 1]);
						el.parent().addClass(roundRect[roundRect.length - 1]);
					}
				}
			}
			if(textClass[index]){
				el.html("<span>" + Math.round(el.text()) + "%</span>");
				el.children("span").addClass(textClass[index]);
			}
			else{
				el.html("&nbsp;");
			}
		});
	});

  };
})( jQuery );

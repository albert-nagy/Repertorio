function getForm(what, id) {
  $.ajax({
      type: 'POST',
      url: '/infotoedit?what='+what+'&id='+id,
      contentType: 'application/octet-stream; charset=utf-8',
      success: function(result) {
         
          if (what == 'bio')
                {
                form = `<form id="editform" action="javascript:void(0)" method="post" onsubmit="editContent(this, 'bio', '`+id+`')">
                <textarea name="edit_bio">`+result+`</textarea>
                <button type="submit" class="edit">Submit</button>
                <button type="reset" class="cancel" onclick="Cancel('bio','`+id+`')">Cancel</button>
                </form>`;
                }
          document.getElementById(what).innerHTML = form;
      }
      
  }); 
  }

function editContent(form, what, id) {
  if (what == 'bio')
    content = form.elements['edit_bio'].value;
  $.ajax({
      type: 'POST',
      url: '/edit?action=edit&what='+what+'&id='+id+'&text='+encodeURIComponent(content),
      contentType: 'application/octet-stream; charset=utf-8',
      success: function(result) {
         
          if (what == 'bio')
                {
                text = `<p>`+result+`</p>
                <button type="submit" class="edit" onclick="getForm('bio', '`+id+`');">Edit</button>`;
                }
          document.getElementById(what).innerHTML = text;
      }
      
  }); 
  }

  function Cancel(what,id) {
  $.ajax({
      type: 'POST',
      url: '/edit?action=cancel&what='+what,
      contentType: 'application/octet-stream; charset=utf-8',
      success: function(result) {
          if (what == 'bio')
                {
                text = `<p>`+result+`</p>
                <button type="submit" class="edit" onclick="getForm('bio', '`+id+`');">Edit</button>`;
                }
          document.getElementById(what).innerHTML = text;
      }
      
  }); 
  }
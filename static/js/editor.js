function getForm(what, id) {
  $.ajax({
      type: 'POST',
      url: '/infotoedit?what='+what+'&id='+id,
      contentType: 'application/octet-stream; charset=utf-8',
      success: function(result) {replacePart(what,result,id,1);}
      
  }); 
  }

function editContent(form, what, id) {
  if (what == 'bio')
    content = form.elements['edit_bio'].value;
  $.ajax({
      type: 'POST',
      url: '/edit?action=edit&what='+what+'&id='+id+'&text='+encodeURIComponent(content),
      contentType: 'application/octet-stream; charset=utf-8',
      success: function(result) {replacePart(what,result,id,0);}
  }); 
  }

  function Cancel(what,id) {
  $.ajax({
      type: 'POST',
      url: '/edit?action=cancel&what='+what,
      contentType: 'application/octet-stream; charset=utf-8',
      success: function(result) {replacePart(what,result,id,0);}
  }); 
  }

  function replacePart(what,result,id,form)
    {
    if (what == 'bio')
      {
      if (form == 0)
         text = `<p>`+result+`</p>
          <button type="submit" class="edit" onclick="getForm('bio', '`+id+`');">Edit Bio</button>`;
      else
        text = `<form id="editform" action="javascript:void(0)" method="post" onsubmit="editContent(this, 'bio', '`+id+`')">
                <textarea name="edit_bio">`+result+`</textarea>
                <button type="submit" class="edit">Save</button>
                <button type="reset" class="cancel" onclick="Cancel('bio','`+id+`')">Cancel</button>
                </form>`;
      }
    document.getElementById(what).innerHTML = text;
    }
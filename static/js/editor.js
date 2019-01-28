function authOperation(result)
  {
  var response = JSON.parse(result);
  if (response[0] == 0)
    window.location.href = page;
  else if (response[0] == 1)
    return response[1];
  } 

function getForm(what, id) {
  $.ajax({
      type: 'POST',
      url: '/infotoedit?what='+what+'&id='+id,
      contentType: 'application/octet-stream; charset=utf-8',
      success: function(result) {replacePart(what,result,id,1);}
      
  }); 
  }

function editContent(form, what, id) {
  var content;
  if (what == 'bio')
    content = '&text='+encodeURIComponent(form.elements['edit_bio'].value);
  else if (what == 'contact')
    content = '&phone='+encodeURIComponent(form.elements['phone'].value)+'&address='+encodeURIComponent(form.elements['address'].value);
  else if (what == 'email_privacy')
    content = '';
  $.ajax({
      type: 'POST',
      url: '/edit?action=edit&what='+what+'&id='+id+content,
      contentType: 'application/octet-stream; charset=utf-8',
      success: function(result) {replacePart(what,result,id,0);}
  }); 
  }

  function Cancel(what,id) {
  $.ajax({
      type: 'POST',
      url: '/edit?action=cancel&what='+what+'&id='+id,
      contentType: 'application/octet-stream; charset=utf-8',
      success: function(result) {replacePart(what,result,id,0);}
  }); 
  }

  function replacePart(what,result,id,form)
    {
    var response = authOperation(result);
    var text;
    if (what == 'bio')
      {
      if (form == 0)
        text = `<p>`+response+`</p>
          <button type="submit" class="edit" onclick="getForm('bio', '`+id+`');">Edit Bio</button>`;
      else
        text = `<form action="javascript:void(0)" method="post" onsubmit="editContent(this, 'bio', '`+id+`')">
                <textarea name="edit_bio">`+response+`</textarea>
                <button type="submit" class="edit">Save</button>
                <button type="reset" class="cancel" onclick="Cancel('bio','`+id+`')">Cancel</button>
                </form>`;
      }
    else if (what == 'contact')
      {
      var phone = (response[0] != null) ? response[0]:``;
      var address = (response[1] != null) ? response[1]:``;
      if (form == 1)
        {
        text = `<form action="javascript:void(0)" method="post" onsubmit="editContent(this, 'contact', '`+id+`')">
                <p><label><strong>Phone: </strong><input type="text" name="phone" value="`+phone+`" /></label></p>
                <p><label><strong>Address: </strong><input type="text" name="address" value="`+address+`" /></label></p>
                <button type="submit" class="edit">Save</button>
                <button type="reset" class="cancel" onclick="Cancel('contact','`+id+`')">Cancel</button>
                </form>`;
        }
      else
        {
        if (phone == ``)
          phone = `-`;
        if (address == ``)
          address = `-`;
        text = `<p><strong>Phone: </strong>`+phone+`</p>
                <p><strong>Address: </strong>`+address+`</p>
                <button type="submit" class="edit" onclick="getForm('contact','`+id+`');">Edit Contact Info</button>`
        }
      }
    else if (what == 'email_privacy')
      text = response;
    else if (what == 'add_work')
      {
      text = `<form action="javascript:void(0)" method="post" onsubmit="editContent(this, 'add_work', '`+id+`')">
                <p><label><strong>Composer name: </strong><input type="text" name="composer" value="" /></label>
                <label> <strong>Title: </strong><input type="text" name="title" value="" /></label> 
                <label><strong>Duration: </strong><input type="text" name="duration" value="" /> min</label></p>
                <p><label><strong>Instrument: </strong><select id="instrument">
                `+ response[0] +`</select></label> 
                <label>`+ response[1] +`</label></p>
                <button type="submit" class="edit">Save</button>
                <button type="reset" class="cancel" onclick="Cancel('add_work','`+id+`')">Cancel</button>
                </form>`;
      }
    document.getElementById(what).innerHTML = text;
    }
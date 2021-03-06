var select1;
var select2;

function authOperation(result)
  {
  var response = JSON.parse(result);
  if (response[0] == 0)
    window.location.href = page;
  else if (response[0] == 1)
    return response[1];
  } 

function getForm(what, id) 
  {
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
    content = '&text='+encodeURIComponent(form.elements['edit_bio'].value.trim());
  else if (what == 'contact')
    content = '&phone='+encodeURIComponent(form.elements['phone'].value.trim())+'&address='+encodeURIComponent(form.elements['address'].value.trim());
  else if (what == 'email_privacy')
    content = '';
  // If it is a category
  else if (what.substring(0,2) == 'c_')
    {
    var name = form.elements['category'].value.trim();
    if (!name)
      {
      alert("Please fill out the category name!"); 
      return
      }
    content = '&name='+encodeURIComponent(name);
    }
  // If it is an instrument
  else if (what.substring(0,2) == 'i_')
    {
    var name = form.elements['instrument'].value.trim();
    if (!name)
      {
      alert("Please fill out the instrument name!"); 
      return
      }
    content = '&name='+encodeURIComponent(name);
    }

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

// Add new work to repertoire or edit an existing one
  function addWork(form,id,work)
    {
    var composer = form.elements['composer'].value.trim();
    var title = form.elements['title'].value.trim();
    var duration = form.elements['duration'].value.trim();
    var category;
    if (document.getElementById('category'))
      {
      var select = document.getElementById('category');
      category = encodeURIComponent(select.options[select.selectedIndex].value);
      }
    else
      category = encodeURIComponent(form.elements['category'].value.trim());
    var instrument;
    if (document.getElementById('instrument'))
      {
      var select = document.getElementById('instrument');
      instrument = encodeURIComponent(select.options[select.selectedIndex].value);
      }
    else
      instrument = encodeURIComponent(form.elements['instrument'].value.trim());
    
    if (!composer||!title||!duration||!category||!instrument)
      alert("Please fill out all fields!");
    else if (isNaN(duration)||Math.round(duration)<1)
      alert("Duration has to be a number greater than 0!");
    else
      {
      var content = '&composer='+encodeURIComponent(composer)+'&title='+encodeURIComponent(title)+
      '&duration='+Math.round(duration)+'&category='+category+'&instrument='+instrument;
      if (work > 0)
        content += '&work='+work;
      $.ajax({
        type: 'POST',
        url: '/add_work?id='+id+content,
        contentType: 'application/octet-stream; charset=utf-8',
        success: function(result) {replacePart('repertoire',result,id,0);}
      });
      }
    }

  function replacePart(what,result,id,form)
    {
    if (what != 'cat_selector')
      var response = authOperation(result);
    var text;
    if (what == 'bio')
      {
      if (form == 0)
        text = `<p>`+response+`</p>
          <button type="submit" class="edit edit-contact" onclick="getForm('bio', '`+id+`');">Edit Bio</button>`;
      else
        text = `<form action="javascript:void(0)" method="post" onsubmit="editContent(this, 'bio', '`+id+`')">
                <textarea name="edit_bio">`+response+`</textarea>
                <button type="submit" class="add edit-contact">Save</button>
                <button type="reset" class="cancel edit-contact" onclick="Cancel('bio','`+id+`')">Cancel</button>
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
                <button type="submit" class="add edit-contact">Save</button>
                <button type="reset" class="cancel edit-contact" onclick="Cancel('contact','`+id+`')">Cancel</button>
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
                <button type="submit" class="edit edit-contact" onclick="getForm('contact','`+id+`');">Edit Contact Info</button>`
        }
      }
    else if (what == 'email_privacy')
      text = response;
    else if (what == 'add_work')
      {
      if (form == 1)
        text = response;
      else
        text = `<button class="add" onclick="getForm('add_work','`+id+`');">+ Add Work to your Repertoire</button>`;
      }
    else if (what == 'repertoire')
      {
      document.getElementById('instruments').innerHTML = response[0]; 
      text = response[1];
      }
    else if (what == 'cat_selector')
      {
        if (result == 0)
        {
        select1 = document.getElementById('cat_selector').innerHTML;
        text = `<strong>Create Category: </strong><br />
          <input type="text" name="category" value="" /> 
          <button class="cancel" type="button" onclick="replacePart('cat_selector',1,0,0)">Select an existing category instead</button>`; 
        }
        else
          text = select1;
      }
    else if (what == 'inst_selector')
      {
        if (result == 0)
        {
        select2 = document.getElementById('inst_selector').innerHTML;
        text = `<strong>Create Instrument: </strong><br />
          <input type="text" name="instrument" value="" /> 
          <button class="cancel" type="button" onclick="replacePart('inst_selector',1,0,0)">Select an instrument from the list</button>`; 
        }
        else
          text = select2;      
      }
    // If it is a category
    else if (what.substring(0,2) == 'c_')
      {
      if (form == 1)
        text = `<form action="javascript:void(0)" method="post" onsubmit="editContent(this, '`+what+`', '`+id+`')">
                <input type="text" name="category" value="`+response+`" />
                <button type="submit" class="add">Save</button>
                <button type="reset" class="cancel" onclick="Cancel('`+what+`','`+id+`')">Cancel</button>
                </form>`;  
      else
        {
        // Reload the whole repertoire list to update categories in the add_work form as well
        replacePart('repertoire',result,id,0);
        return
        }
      }
    else if (what == 'instrument_list')
      {
      if (typeof response == 'object')
        {
        if (response[1] == 1)
          {
          alert("There is already an instrument with this name!");
          return
          }
        else if (response[1] == 2)
          {
          alert("You are not allowed to modify the instrument's name.\nSomeone else is listing it already in their repertoire.");
          return
          }
        text = response[0]
        }
      else
        text = response;
      }
    else if (what.substring(0,2) == 'i_')
      {
      if (form == 1)
        text = `<form action="javascript:void(0)" method="post" onsubmit="editContent(this, '`+what+`', '`+id+`')">
                <input type="text" name="instrument" value="`+response+`" />
                <button type="submit" class="add">Save</button>
                <button type="reset" class="cancel" onclick="Cancel('`+what+`','`+id+`')">Cancel</button>
                </form>`;  
      else
        {
        // Reload the whole instrument list
        replacePart('instrument_list',result,id,0);
        return
        }
      }
    document.getElementById(what).innerHTML = text;
    }

function delWork(work,id)
 {
  if (confirm("Are you sure to delete this work?"))
  {
  $.ajax({
        type: 'POST',
        url: '/del_work?id='+id+'&work='+work,
        contentType: 'application/octet-stream; charset=utf-8',
        success: function(result) {replacePart('repertoire',result,id,0);}
      });

  }
 }

 function workToEdit(work, id) {
  $.ajax({
      type: 'POST',
      url: '/worktoedit?work='+work+'&id='+id,
      contentType: 'application/octet-stream; charset=utf-8',
      success: function(result) {replacePart('add_work',result,id,1);
      window.location.href = "#repertoire";}    
  }); 
  }

function delCat(cat,id)
 {
  if (confirm("Are you sure to delete this category together with its content?"))
  {
  $.ajax({
        type: 'POST',
        url: '/del_cat?id='+id+'&category='+cat,
        contentType: 'application/octet-stream; charset=utf-8',
        success: function(result) {replacePart('repertoire',result,id,0);}
      });
  }
 }

 function delInstrument(instrument,id)
 {
  if (confirm("Are you sure to delete this instrument?"))
  {
  $.ajax({
        type: 'POST',
        url: '/del_instr?id='+id+'&instrument='+instrument,
        contentType: 'application/octet-stream; charset=utf-8',
        success: function(result) {replacePart('instrument_list',result,id,0);}
      });
  }
 }

 function delProfile(id)
 {
  if (confirm("Are you sure to delete your profile?\nAll your personal data and repertoire will get lost irrevocably!!!"))
  {
  $.ajax({
        type: 'POST',
        url: '/del_profile?id='+id,
        contentType: 'application/octet-stream; charset=utf-8',
        success: function(result) {
          response = authOperation(result);
          if (response == 1)
            window.location.href = '/';
        }
      });
  }
 }

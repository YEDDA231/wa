import sys
sys.path.insert(0,'db/')
from flask import Flask,render_template,request,redirect,url_for,session,flash
from dbhelper import *

app:any = Flask(__name__)
app.secret_key='599b6aa8fc0f4d08a5380df764f95656'
initdb()


@app.after_request
def after_request(response)->None:
    response.headers['Cache-Control']="no-cache,no-store,must-revalidate"
    return response


def requirelogin():
    if 'email' not in session:
        flash("Login Properly")
        return redirect(url_for('index'))
    return None


def blanknone(value:str):
    if value is None or str(value).strip()=="":
        return None
    return value


@app.route("/logout")
def logout()->None:
    session.pop('email',None)
    session.clear()
    return redirect(url_for('index'))


# (-----------------) edit login
@app.route("/login",methods=['POST'])
def login()->None:
    email:str = request.form['email']
    password:str = request.form['password']
    user:list = getrecord('users',email=email,password=password)
    if len(user)>0:
        session['email']=email
        flash("Login success")
        return redirect(url_for('main'))
    else:
        flash("Login Failed")
        return redirect(url_for('index'))
# (-----------------) end


@app.route("/")
def index()->None:
    return render_template("index.html",accounts=getall('users'))


@app.route("/main")
def main()->None:
    guard = requirelogin()
    if guard:
        return guard
    # (-----------------) edit search
    q:str = request.args.get('q','').strip()
    # (-----------------) end
    products:list = getinventory(q)
    categories:list = getall('categories')
    suppliers:list = getall('suppliers')
    allitems:list = getall('products')
    low:int = 0
    for item in allitems:
        # (-----------------) edit low stock
        if int(item['quantity'])<=5:
            low += 1
        # (-----------------) end
    return render_template(
        "main.html",
        products=products,
        categories=categories,
        suppliers=suppliers,
        q=q,
        total=len(allitems),
        low=low
    )


@app.route("/saveproduct",methods=['POST'])
def saveproduct()->None:
    guard = requirelogin()
    if guard:
        return guard
    # (-----------------) edit items
    savetype:str = request.form['savetype']
    sku:str = request.form['sku'].strip()
    name:str = request.form['name'].strip()
    category_id:str = blanknone(request.form['category_id'])
    supplier_id:str = blanknone(request.form['supplier_id'])
    price:str = request.form['price'].strip()
    quantity:str = request.form['quantity'].strip()
    unit:str = request.form['unit'].strip()
    # (-----------------) end
    if unit=="":
        unit = "pcs"
    if sku=="" or name=="" or price=="" or quantity=="":
        flash("Fill all fields")
        return redirect(url_for('main'))
    try:
        price_val:float = float(price)
        qty_val:int = int(quantity)
    except ValueError:
        flash("Price and quantity must be numbers")
        return redirect(url_for('main'))
    if price_val<0 or qty_val<0:
        flash("Price and quantity cannot be negative")
        return redirect(url_for('main'))
    if savetype=="0":
        ok:bool = addrecord(
            'products',
            sku=sku,
            name=name,
            category_id=category_id,
            supplier_id=supplier_id,
            price=price_val,
            quantity=qty_val,
            unit=unit
        )
        if ok:
            row:list = getrecord('products',sku=sku)
            if len(row)>0:
                addrecord('stock_logs',product_id=row[0]['id'],change_qty=qty_val,action='IN',note='Initial stock')
            flash("New Item Added")
        else:
            flash("Error Adding Item")
        return redirect(url_for('main'))
    if savetype=="1":
        item_id:str = request.form['id']
        old:list = getrecord('products',id=item_id)
        old_qty:int = int(old[0]['quantity']) if len(old)>0 else 0
        updaterecord(
            'products',
            id=item_id,
            sku=sku,
            name=name,
            category_id=category_id,
            supplier_id=supplier_id,
            price=price_val,
            quantity=qty_val,
            unit=unit
        )
        saved:list = getrecord('products',id=item_id)
        saved_ok:bool = False
        if len(saved)>0:
            row:any = saved[0]
            same_category:bool = str(row['category_id'] or '')==str(category_id or '')
            same_supplier:bool = str(row['supplier_id'] or '')==str(supplier_id or '')
            saved_ok = str(row['sku'])==sku and str(row['name'])==name and float(row['price'])==price_val and int(row['quantity'])==qty_val and str(row['unit'] or '')==unit and same_category and same_supplier
        if saved_ok:
            delta:int = qty_val-old_qty
            if delta!=0:
                addrecord('stock_logs',product_id=item_id,change_qty=delta,action='ADJUST',note='Quantity updated')
            flash("Item Updated")
        else:
            flash("Error Updating Item")
        return redirect(url_for('main'))
    flash("Error Saving Item")
    return redirect(url_for('main'))


@app.route("/deleteproduct",methods=['GET'])
def deleteproduct()->None:
    guard = requirelogin()
    if guard:
        return guard
    item_id:str = request.args.get('id')
    deleterecord('stock_logs',product_id=item_id)
    ok:bool = deleterecord('products',id=item_id)
    if ok:
        flash("Item Deleted")
    else:
        flash("Error Deleting Item")
    return redirect(url_for('main'))


@app.route("/categories")
def categories()->None:
    guard = requirelogin()
    if guard:
        return guard
    q:str = request.args.get('q','').strip()
    # (-----------------) edit category search
    rows:list = searchrecord('categories',['name'],q)
    # (-----------------) end
    return render_template("categories.html",categories=rows,q=q)


@app.route("/savecategory",methods=['POST'])
def savecategory()->None:
    guard = requirelogin()
    if guard:
        return guard
    # (-----------------) edit category
    savetype:str = request.form['savetype']
    name:str = request.form['name'].strip()
    # (-----------------) end
    if name=="":
        flash("Fill all fields")
        return redirect(url_for('categories'))
    if savetype=="0":
        ok:bool = addrecord('categories',name=name)
        flash("Category Added" if ok else "Error Adding Category")
    else:
        updaterecord('categories',id=request.form['id'],name=name)
        saved:list = getrecord('categories',id=request.form['id'],name=name)
        flash("Category Updated" if len(saved)>0 else "Error Updating Category")
    return redirect(url_for('categories'))


@app.route("/deletecategory",methods=['GET'])
def deletecategory()->None:
    guard = requirelogin()
    if guard:
        return guard
    category_id:str = request.args.get('id')
    used:list = getrecord('products',category_id=category_id)
    if len(used)>0:
        flash("Category is used by items")
        return redirect(url_for('categories'))
    ok:bool = deleterecord('categories',id=category_id)
    flash("Category Deleted" if ok else "Error Deleting Category")
    return redirect(url_for('categories'))


@app.route("/suppliers")
def suppliers()->None:
    guard = requirelogin()
    if guard:
        return guard
    q:str = request.args.get('q','').strip()
    # (-----------------) edit supplier search
    rows:list = searchrecord('suppliers',['name','contact','email'],q)
    # (-----------------) end
    return render_template("suppliers.html",suppliers=rows,q=q)


@app.route("/savesupplier",methods=['POST'])
def savesupplier()->None:
    guard = requirelogin()
    if guard:
        return guard
    # (-----------------) edit supplier
    savetype:str = request.form['savetype']
    name:str = request.form['name'].strip()
    contact:str = request.form['contact'].strip()
    email:str = request.form['email'].strip()
    # (-----------------) end
    if name=="":
        flash("Fill all fields")
        return redirect(url_for('suppliers'))
    if savetype=="0":
        ok:bool = addrecord('suppliers',name=name,contact=contact,email=email)
        flash("Supplier Added" if ok else "Error Adding Supplier")
    else:
        updaterecord('suppliers',id=request.form['id'],name=name,contact=contact,email=email)
        saved:list = getrecord('suppliers',id=request.form['id'],name=name,contact=contact,email=email)
        flash("Supplier Updated" if len(saved)>0 else "Error Updating Supplier")
    return redirect(url_for('suppliers'))


@app.route("/deletesupplier",methods=['GET'])
def deletesupplier()->None:
    guard = requirelogin()
    if guard:
        return guard
    supplier_id:str = request.args.get('id')
    used:list = getrecord('products',supplier_id=supplier_id)
    if len(used)>0:
        flash("Supplier is used by items")
        return redirect(url_for('suppliers'))
    ok:bool = deleterecord('suppliers',id=supplier_id)
    flash("Supplier Deleted" if ok else "Error Deleting Supplier")
    return redirect(url_for('suppliers'))


@app.route("/logs")
def logs()->None:
    guard = requirelogin()
    if guard:
        return guard
    q:str = request.args.get('q','').strip()
    rows:list = getstocklogs(q)
    return render_template("logs.html",logs=rows,q=q)


if __name__=="__main__":
    app.run(debug=True)

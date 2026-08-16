Each User will have 
- UserId - Random guid generating for every new user 
- Name - Name of the user
- Email (Optional - depends on auth type)
- Phone No (Optional - depends on auth type)
- One company name - string field 
- Stock Items - Seperate table 
- Invoice - Seperate table
- Customers - Seperate table

Each Invoice 
- unique id/ invoice no. (can start with 0)
- Customer Name
- Array of invoice items - [name,quantity,discount%,price per item,total discount, date]
- Total Amount

Each Stock Item
- Name - string
- Quantity - number
- Cost Price - decimal / double
- Selling Price - decimal / double

- Each customer 
- Name 
- Invoice associated with it - Array of invoice id 
- Balance amount




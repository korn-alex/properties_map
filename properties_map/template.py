""" template for database """
from dataclasses import dataclass
from collections import namedtuple

@dataclass
class Column:
    name:str
    type:str
    extra:str = ''

@dataclass
class Table:
    name:str

@dataclass
class Template:
    table:Table
    column:[Column]
    extra_statements:list=None

    def column_names(self):
        """Makes names from column names.

        Returns
        -------
        list
            column_name
        """
        return [c.name for c in self.column]

    def _value_str(self) -> str:
        """Makes values string for sql.

        Returns
        -------
        str
            `"VALUES(?,?, ...)"`
        """
        _v = ('?,'*len(self.column))[:-1]
        v = f'VALUES({_v})'
        return v

    def get_create_table_sql(self) -> str:
        """Makes SQL query for creating the table from this template.
        
        `CREATE TABLE Table(col_1 type PRIMARYY KEY, col_2 type, ...)`

        Returns
        -------
        str
            sql_query
        """
        create = f'CREATE TABLE {self.table.name}('
        _cols = [f'{c.name} {c.type} {c.extra}'.rstrip() for c in  self.column]
        # eg: FOREIGN KEY statement
        if self.extra_statements is not None:
            _cols += self.extra_statements
        columns = ','.join(_cols)+');'
        sql = create+columns
        return sql

    def get_insert_sql(self) -> str:
        """Makes sql statement from template.
        
        `INSERT INTO Table(col_1,col_2, ...) values (?,?, ...)`

        Returns
        -------
        str
            sql_insert    
        """
        insert = f'INSERT INTO {self.table.name}'
        _cols = [f'{c.name}'.rstrip() for c in  self.column]
        columns = ','.join(_cols)
        values = self._value_str()
        sql = f'{insert} ({columns}) {values};'
        return sql
    
    def get_select_sql(self, sql_extra:str=None) -> str:
        """Makes sql statement from template.
        
        `SELECT key1, key2, ... FROM Table` + `sql_extra`

        Returns
        -------
        str
            sql_select
        """
        sql_extra = sql_extra if sql_extra else ''
        names = self.column_names()
        sql_cols = ','.join(names)
        sql = f'SELECT {sql_cols} FROM {self.table.name} ' + sql_extra
        return sql

_apartment_columns = [
    Column('id','INT','PRIMARY KEY'),
    Column('title','TEXT'),
    Column('address','TEXT'),
    Column('preview_image','TEXT'),
    Column('expose','TEXT'),
    Column('description','TEXT'),
    Column('total_rent','REAL'),
    Column('cold_rent','REAL'),
    Column('add_costs','REAL'),
    Column('deposit','TEXT'),
    Column('living_area','TEXT'),
    Column('rooms','TEXT'),
    Column('coordinates','TEXT'),
    Column('energy_usage','REAL'),
    Column('available','TEXT'),
    Column('extras','TEXT'),
    Column('parsed','TEXT'),
    ]
apartment_template = Template(Table('Apartment'), _apartment_columns)


_image_columns = [
    Column('id','INT','PRIMARY KEY'),
    Column('src', 'TEXT' ),
    Column('caption','TEXT'),
    Column('is_floorplan', 'INT'),
    Column('img_bytes', 'BLOB'),
    Column('apartment_id', 'INT' ),
]
_image_extra_statements = [f'FOREIGN KEY(apartment_id) REFERENCES {apartment_template.table.name}(id)']
image_template = Template(Table('Image'), _image_columns, _image_extra_statements)
ApartmentTemplateCollection = namedtuple('Template',['apartment','image'])
apartment_db_templates = ApartmentTemplateCollection(apartment=apartment_template, image=image_template)


# for sample use
_website_columns = [
    Column('id', 'INT','PRIMARY KEY'),
    Column('website', 'TEXT'),
    Column('url', 'TEXT'),
    Column('html', 'TEXT'),
]
_preview_columns = [
    Column('id', 'INT','PRIMARY KEY'),
    Column('website', 'TEXT'),
    Column('url', 'TEXT'),
    Column('html', 'TEXT'),
]
_expose_columns = [
    Column('id', 'INT','PRIMARY KEY'),
    Column('website', 'TEXT'),
    Column('url', 'TEXT'),
    Column('html', 'TEXT'),
]

_web_template = Template(Table('web'),_website_columns)
_preview_template = Template(Table('preview'),_preview_columns)

_expose_extra_statements = [f'FOREIGN KEY(id) REFERENCES {_preview_template.table.name}(id)']
_expose_template = Template(Table('expose'),_expose_columns,extra_statements=_expose_extra_statements)

_SiteDataCollection = namedtuple('Template',['web','expose','preview'])
site_db_templates = _SiteDataCollection(web=_web_template, preview=_preview_template, expose=_expose_template)
# -*- coding: utf-8 -*-
from AccessControl import ClassSecurityInfo
from OFS.ObjectManager import ObjectManager
from archetypes.querywidget.field import QueryField
from archetypes.querywidget.widget import QueryWidget
from plone.app.contentlisting.interfaces import IContentListing
from Products.ATContentTypes.content import document, schemata, folder
from Products.Archetypes import atapi
from Products.Archetypes.atapi import (BooleanField,
                                       BooleanWidget,
                                       IntegerField,
                                       LinesField,
                                       IntegerWidget,
                                       InAndOutWidget,
                                       StringField,
                                       StringWidget)
from Products.CMFCore.permissions import ModifyPortalContent, View
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import INonStructuralFolder
from zope.interface import implements

from plone.app.collection import PloneMessageFactory as _
from plone.app.collection.config import ATCT_TOOLNAME, PROJECTNAME
from plone.app.collection.interfaces import ICollection
from plone.app.collection.marshaller import CollectionRFC822Marshaller

CollectionSchema = folder.ATFolderSchema.copy() + document.ATDocumentSchema.copy() + atapi.Schema((

    BooleanField('acquireCriteria',
        required=False,
        mode="rw",
        default=False,
        write_permission=ModifyPortalContent,
        widget=BooleanWidget(
            label=_(u'label_inherit_criteria', default=u'Inherit Criteria'),
            description=_(
                u'help_inherit_collection_criteria',
                default=u"Narrow down the search results from the parent Collection(s) "
                        u"by using the criteria from this Collection."),
            # Only show when the parent object is a Collection also.
            condition="python:object.aq_parent.portal_type == 'Collection'"
            ),
        ),

    QueryField(
        name='query',
        widget=QueryWidget(
            label=_(u"Search terms"),
            description=_(u"Define the search terms for the items you want to "
                          u"list by choosing what to match on. "
                          u"The list of results will be dynamically updated."),
            ),
        validators=('javascriptDisabled',)
        ),

    StringField(
        name='sort_on',
        required=False,
        mode='rw',
        default='sortable_title',
        widget=StringWidget(
            label=_(u'Sort the collection on this index'),
            description='',
            visible=False,
            ),
        ),

    BooleanField(
        name='sort_reversed',
        required=False,
        mode='rw',
        default=False,
        widget=BooleanWidget(
            label=_(u'Sort the results in reversed order'),
            description='',
            visible=False,
            ),
        ),

    IntegerField(
        name='b_size',
        required=False,
        mode='rw',
        default=30,
        widget=IntegerWidget(
            label=_(u'Limit Results by Page'),
            description=_(u"Specify the number of items to show by page.")
            ),
        validators=('isInt',)
        ),

    IntegerField(
        name='limit',
        required=False,
        mode='rw',
        default=1000,
        widget=IntegerWidget(
            label=_(u'Limit Search Results'),
            description=_(u"Specify the maximum number of items to show.")
            ),
        validators=('isInt',)
        ),

    LinesField(
        name='customViewFields',
        required=False,
        mode='rw',
        default=('Title', 'Creator', 'Type', 'ModificationDate'),
        vocabulary='listMetaDataFields',
        enforceVocabulary=True,
        write_permission=ModifyPortalContent,
        widget=InAndOutWidget(
            label=_(u'Table Columns'),
            description=_(u"Select which fields to display when "
                          u"'Tabular view' is selected in the display menu.")
            ),
        ),
))

# Use the extended marshaller that understands queries
CollectionSchema.registerLayer("marshall", CollectionRFC822Marshaller())

CollectionSchema.moveField('query', after='description')
CollectionSchema.moveField('acquireCriteria', before='query')
if 'presentation' in CollectionSchema:
    CollectionSchema['presentation'].widget.visible = False
CollectionSchema['tableContents'].widget.visible = False


schemata.finalizeATCTSchema(
    CollectionSchema,
    folderish=True,
    moveDiscussion=False)


class Collection(folder.ATFolder, document.ATDocumentBase, ObjectManager):
    """A (new style) folderish Plone Collection"""
    implements(ICollection, INonStructuralFolder)

    meta_type = "Collection"
    schema = CollectionSchema

    security = ClassSecurityInfo()

    security.declareProtected(View, 'listMetaDataFields')
    def listMetaDataFields(self, exclude=True):
        """Return a list of metadata fields from portal_catalog.
        """
        tool = getToolByName(self, ATCT_TOOLNAME)
        return tool.getMetadataDisplay(exclude)

    security.declareProtected(View, 'results')
    def results(self, batch=True, b_start=0, b_size=0, sort_on=None, brains=False, custom_query={}):
        """Get results"""
        batch_size = self.getB_size()
        if sort_on is None:
            sort_on = self.getSort_on()
        if b_size == 0 and not batch_size and not batch:
            b_size = self.getLimit()
        if b_size == 0 and batch_size and batch:
            b_size = batch_size
        return self.getQuery(batch=batch, b_start=b_start, b_size=b_size, sort_on=sort_on, brains=brains, custom_query=custom_query)

    security.declareProtected(View, 'hasSubcollections')
    def hasSubcollections(self):
        """Returns true if subcollectionsview have been created on
        this collection.
        """
        val = self.objectIds(self.meta_type)
        return bool(val)

    security.declareProtected(View, 'allowAddSubcollection')
    def allowAddSubcollection(self):
        """Are subcollections allowed?

        By default we allow it, though the UI may not show anything.
        Also, some permissions will normally be checked as well.
        """
        return True

    # for BBB with ATTopic
    security.declareProtected(View, 'queryCatalog')
    def queryCatalog(self, batch=True, b_start=0, b_size=30, sort_on=None, **kwargs):
        return self.results(batch, b_start, b_size, sort_on=sort_on, brains=True, custom_query=kwargs)

    # for BBB with ATTopic
    # This is used in Plone 4.2 but no longer in Plone 4.3
    security.declareProtected(View, 'synContentValues')
    def synContentValues(self):
        syn_tool = getToolByName(self, 'portal_syndication')
        limit = int(syn_tool.getMaxItems(self))
        return self.queryCatalog(batch=False, b_size=limit)[:limit]

    security.declareProtected(View, 'selectedViewFields')
    def selectedViewFields(self):
        """Get which metadata field are selected"""
        _mapping = {}
        for field in self.listMetaDataFields().items():
            _mapping[field[0]] = field
        return [_mapping[field] for field in self.customViewFields]

    security.declareProtected(View, 'getFoldersAndImages')
    def getFoldersAndImages(self):
        """Get folders and images"""
        catalog = getToolByName(self, 'portal_catalog')
        results = self.results(batch=False)

        _mapping = {'results': results, 'images': {}, 'others': []}
        portal_atct = getToolByName(self, 'portal_atct')
        image_types = getattr(portal_atct, 'image_types', [])

        for item in results:
            item_path = item.getPath()
            if item.isPrincipiaFolderish:
                query = {
                    'portal_type': image_types,
                    'path': item_path,
                }
                _mapping['images'][item_path] = IContentListing(catalog(query))
            elif item.portal_type in image_types:
                _mapping['images'][item_path] = [item, ]
            else:
                _mapping['others'].append(item._brain)

        _mapping['total_number_of_images'] = sum(map(len,
                                                _mapping['images'].values()))
        return _mapping


atapi.registerType(Collection, PROJECTNAME)

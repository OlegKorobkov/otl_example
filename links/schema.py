import graphene
from graphene_django import DjangoObjectType
from users.schema import UserType
from graphql import GraphQLError
from django.db.models import Q
from opentelemetry import trace
from hackernews.celery import add as task_add

from .models import Link, Vote


tracer = trace.get_tracer("my.tracer")


class LinkType(DjangoObjectType):
    class Meta:
        model = Link


class VoteType(DjangoObjectType):
    class Meta:
        model = Vote


class Query(graphene.ObjectType):
    # Add the first and skip parameters
    links = graphene.List(
        LinkType,
        search=graphene.String(),
        first=graphene.Int(),
        skip=graphene.Int(),
    )
    votes = graphene.List(VoteType)

    # Use them to slice the Django queryset
    def resolve_links(self, info, search=None, first=None, skip=None, **kwargs):
        qs = Link.objects.all()

        if search:
            filter = (
                Q(url__icontains=search) |
                Q(description__icontains=search)
            )
            qs = qs.filter(filter)

        if skip:
            qs = qs[skip:]

        if first:
            qs = qs[:first]

        return qs

    def resolve_votes(self, info, **kwargs):
        return Vote.objects.all()


class CreateLink(graphene.Mutation):
    id = graphene.Int()
    url = graphene.String()
    description = graphene.String()
    posted_by = graphene.Field(UserType)

    class Arguments:
        url = graphene.String()
        description = graphene.String()

    # @tracer.start_as_current_span("mutation - createLink")
    def mutate(self, info, url, description):
        user = None if info.context.user.is_anonymous else info.context.user

        link = Link(url=url, description=description, posted_by=user)
        link.save()

        trace.get_current_span().add_event(
            'Added new link',
            {
                'link_id': link.id,
            }
        )
        trace.get_current_span().set_attribute('zzz','xxx')

        return CreateLink(
            id=link.id,
            url=link.url,
            description=link.description,
            posted_by=link.posted_by,
        )


class CreateVote(graphene.Mutation):
    user = graphene.Field(UserType)
    link = graphene.Field(LinkType)

    class Arguments:
        link_id = graphene.Int()

    @tracer.start_as_current_span("mutation - create-vote")
    def mutate(self, info, link_id):
        user = info.context.user
        if user.is_anonymous:
            raise GraphQLError('You must be logged to vote!')

        link = Link.objects.filter(id=link_id).first()
        if not link:
            raise Exception('Invalid Link!')

        new_vote = Vote.objects.create(
            user=user,
            link=link,
        )

        vote = CreateVote(user=user, link=link)
        current_span = trace.get_current_span()
        current_span.set_attribute("user_name", new_vote.user.username)
        current_span.set_attribute("link_id", new_vote.link.id)
        current_span.add_event('vote created', {'vote_id': new_vote.id})

        task_add.apply_async((5, 8))

        with tracer.start_as_current_span("span - dead"):
            raise Exception('open "qq" or die()')

        return vote


class Mutation(graphene.ObjectType):
    create_link = CreateLink.Field()
    create_vote = CreateVote.Field()
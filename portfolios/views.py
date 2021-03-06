from django.shortcuts import render, redirect
from django.views.generic.edit import CreateView, DeleteView
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.db.models import Q
from django.http import Http404

import datetime

from django import db
import pdb
from dal import autocomplete
from . import forms, models
from django.contrib.auth import get_user_model
User = get_user_model()

# --------------------- Portfolio creation and insertion -----------------------------------

class PortfolioCreate(LoginRequiredMixin, CreateView):
    model = models.Portfolio
    template_name = 'portfolios/portfolio_create_form.html'
    form_class = forms.PortfolioCreationForm

    def get_form_kwargs(self):
        kwargs = super(PortfolioCreate, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('portfolios:manage',args=(self.object.pk,))

class PortfolioListView(LoginRequiredMixin, ListView):
    model = models.Portfolio
    template_name = 'portfolios/portfolio_list.html'
    context_object_name = 'portfolios'

    def get_queryset(self):
        return models.Portfolio.objects.filter(user=self.request.user).order_by('-data_criacao')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        user_portfolios = models.Portfolio.objects.filter(user=self.request.user).order_by('-data_criacao')
        tem_portfolio = list(user_portfolios)

        portfolio_dados =  dict()

        for portfolio in user_portfolios:
            aplicacoes = models.Aplicacao.customObjects.get_aplic_list(portfolio.pk)
            tiposAtivo = models.Aplicacao.customObjects.get_tipoAplicacao_list(portfolio.pk)

            aplicsDetalhe, valoresTipo, valoresTotais = models.Aplicacao.customObjects.get_full_results(portfolio.pk, aplicacoes, tiposAtivo)

            portfolio_dados[portfolio] = valoresTotais

        data['sem_portfolio'] = not bool(tem_portfolio)
        data['portfolio_dados'] = portfolio_dados


        return data


class PortfolioDetailView(LoginRequiredMixin, DetailView):
    model = models.Portfolio
    template_name = 'portfolios/portfolio_detail.html'

class PortfolioDeleteView(LoginRequiredMixin, DeleteView):
    model = models.Portfolio
    success_url = reverse_lazy('portfolios:list')
    template_name = 'portfolios/portfolio_delete.html'
    context_object_name = 'portfolios'


class AtivoAutoComplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            qs = models.AtivoDetalhe.objects.none()

        qs = models.AtivoDetalhe.objects.all()

        tipoAtivo = self.forwarded.get('tipo_ativo', None)
        #pdb.set_trace()
        if tipoAtivo != '3':
            print('not 3')
            qs = qs.filter(grupo_ativo=tipoAtivo)
        else:
            print('its 3')
            qs = qs.filter(grupo_ativo=tipoAtivo).exclude(sigla_ativo__startswith='COMPRA-')

        if self.q:
            qs = qs.filter( Q(desc_ativo__icontains=self.q) |
                            Q(sigla_ativo__icontains=self.q) )

        return qs

    def get_result_label(self, item):
        tipoAtivo = self.forwarded.get('tipo_ativo', None)

        if tipoAtivo == '3':
            return '{}'.format(item.desc_ativo)
        else:
            return '{} - {}'.format(item.desc_ativo,item.sigla_ativo)

    def get_selected_result_label(self, item):
        tipoAtivo = self.forwarded.get('tipo_ativo', None)

        if tipoAtivo == 3:
            return '{}'.format(item.desc_ativo)
        else:
            return '{} - {}'.format(item.desc_ativo,item.sigla_ativo)


@login_required
def manage_portfolios(request, pk):
    portfolio = models.Portfolio.objects.get(pk=pk)
    if request.user != portfolio.user:
        raise Http404('Ops! Essa Página não existe.  =/')
    else:
        PortfolioInlineFormset = inlineformset_factory( models.Portfolio, models.Aplicacao, fk_name='portfolio',
                                                        form= forms.AplicacaoCreationForm,
                                                        extra=1, can_delete=True )
        if request.method =='POST':
            formset = PortfolioInlineFormset(request.POST, request.FILES, instance=portfolio)
            if formset.is_valid():
                formset.save()
                return redirect('portfolios:list')
        else:
            formset = PortfolioInlineFormset(instance=portfolio)
        return render(request, 'portfolios/manage_portfolio.html', {'formset': formset,
                                                                    'portfolio':portfolio})

# --------------------- Portfolio visualization -----------------------------------

@login_required
def rentabilidade_portofolio(request, pk):
    portfolio = get_object_or_404(models.Portfolio, pk=pk)
    if request.user != portfolio.user:
        raise Http404('Ops! Essa Página não existe.  =/')
    else:
        aplicacoes = models.Aplicacao.objects.filter(portfolio=portfolio.pk)

        aplica_preco = dict([(aplic, models.PrecoAtivo.objects.filter(cod_ativo=aplic.ativo.pk).last()) for aplic in aplicacoes])

        sectionChecker = [aplic.ativo.grupo_ativo.desc_grupo for aplic in aplicacoes]



        return render(request, 'portfolios/rentabilidade_portfolio.html', { 'portfolio' : portfolio,
                                                                            'aplicacoes' : aplica_preco,
                                                                            'sections' : sectionChecker} )

@login_required
def portfolio_resumo(request, pk):
    portfolio = get_object_or_404(models.Portfolio, pk=pk)
    if request.user != portfolio.user:
        raise Http404('Ops! Essa Página não existe.  =/')
    else:
        aplicacoes = models.Aplicacao.customObjects.get_aplic_list(portfolio.pk)
        tiposAtivo = models.Aplicacao.customObjects.get_tipoAplicacao_list(portfolio.pk)

        aplicsDetalhe, valoresTipo, valoresTotais = models.Aplicacao.customObjects.get_full_results(portfolio.pk, aplicacoes, tiposAtivo)

        print(aplicsDetalhe)

        return render(request, 'portfolios/resumo.html', { 'portfolio' : portfolio,
                                                           'tipoAtivo': tiposAtivo,
                                                           'aplicacoes' : aplicsDetalhe,
                                                           'dadosTipo' : valoresTipo,
                                                           'dadosTotais': valoresTotais} )
